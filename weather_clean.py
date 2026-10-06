"""
weather_clean.py cleans NOAA GHCN-Daily temperature observations and station metadata for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, substring, trim, when, expr, row_number
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from sedona.spark import SedonaContext
from sedona.spark.sql.st_constructors import ST_Point


# Create a local Spark session using 4 worker threads.
spark = (
    SedonaContext.builder()
    .appName("CityScope Weather Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

sedona = SedonaContext.create(spark)
spark.sparkContext.setLogLevel("WARN")

# Define the schema for NOAA GHCN-Daily observation records. 
weather_schema = StructType(
    [
        StructField("station_id", StringType(), True),
        StructField("date", StringType(), True),
        StructField("element", StringType(), True),
        StructField("value", IntegerType(), True),
        StructField("measurement_flag", StringType(), True),
        StructField("quality_flag", StringType(), True),
        StructField("source_flag", StringType(), True),
        StructField("time_flag", StringType(), True)
    ]
)

# Read the NOAA observation file using the predefined schema.
weather_df = (
    spark.read
    .option("header", "False")
    .schema(weather_schema)
    .option("sep", ",")
    .csv("data/raw/weather/2022.csv.gz")

)

# Keep U.S. temperature observations, convert NOAA values to Fahrenheit,
# and convert the observation date into a Spark date.
weather_cleaned = (
    weather_df
    .filter(
        col("station_id").startswith("US")
        &
        col("element").isin("TAVG","TMAX","TMIN")
    )

    # NOAA uses -9999 to represent missing temperature measurements.
    # Convert valid Celsius values to Fahrenheit and
    # Represent missing measurements as NULL.
    .withColumn("temperature_f", 
                when(col("value") != -9999,
                    ((col("value") / 10.0) * 9/5) + 32         
                ).otherwise(None)
    )

    .withColumn("date", to_date(col("date"), "yyyyMMdd"))
)

# Keep only stations with 2022 temperature observations.
weather_stations = (
    weather_cleaned
    .select("station_id")
    .distinct()
)

# Read the fixed-width NOAA station metadata file.
# Extract station identifiers, geographic coordinates, elevation,
# and station names from the fixed-width records.
stations_raw = (
    spark.read.text("data/raw/weather/ghcnd-stations.txt")
)

# Create a DataFrame containing the parsed station metadata. 
stations_df = (
    stations_raw.select(
        trim(substring(col("value"), 1, 11)).alias("station_id"), 
        trim(substring(col("value"), 13, 8)).cast(DoubleType()).alias("lat"),
        trim(substring(col("value"), 22, 9)).cast(DoubleType()).alias("lng"),
        trim(substring(col("value"), 32, 6)).cast(DoubleType()).alias("elevation"),
        trim(substring(col("value"), 42, 30)).alias("station_name")
    )
)


# Create station points for spatial enrichment.
stations_with_points = (
    stations_df
    .withColumn("point", ST_Point(col("lng"), col("lat")))
)

# Read processed Census Place boundaries for spatial enrichment.
places = (
    sedona.read
    .format("parquet")
    .load("data/processed/places")
    .select(
        "GEOID",
        "NAME",
        "geometry"
    )
)

# Create a representative point for each Census Place.
places_with_points = (
    places
    .withColumn(
        "place_point",
        expr("ST_PointOnSurface(geometry)")
    )
)

# Keep weather stations in and near Texas that have 2022 observations.
texas_stations = (
    stations_with_points
    .join(
        weather_stations,
        "station_id",
        "inner"
    )
    .filter(
        (col("lat") >= 24) &
        (col("lat") <= 38) &
        (col("lng") >= -109) &
        (col("lng") <= -92)
    )
)

# Find the nearest weather station for each Census Place.
station_candidates = (
    places_with_points
    .crossJoin(
        texas_stations.select(
            "station_id",
            "lat",
            "lng",
            "elevation",
            "station_name",
            "point"
        )
    )
    .withColumn(
        "distance",
        expr("ST_DistanceSphere(place_point, point)")
    )
)

# Keep the closest weather station for each Census Place.
window = Window.partitionBy("GEOID").orderBy(col("distance"))

nearest_stations = (
    station_candidates
    .withColumn(
        "rank",
        row_number().over(window)
    )
    .filter(col("rank") == 1)
    .select(
        col("station_id"),
        col("lat"),
        col("lng"),
        col("elevation"),
        col("station_name"),
        col("point"),
        col("GEOID").alias("place_GEOID"),
        col("NAME").alias("place_name")
    )
)

# Join the nearest station back to the weather observations.
weather_enriched = (
    weather_cleaned
    .join(
        nearest_stations,
        "station_id",
        "inner"
    )
    .select(
        col("station_id"),
        col("date"),
        col("element"),
        col("value"),
        col("temperature_f"),
        col("lat"),
        col("lng"),
        col("elevation"),
        col("station_name"),
        col("point"),
        col("place_GEOID"),
        col("place_name")
    )
)

# Final parquet write.
weather_enriched.write.mode("overwrite").parquet(
    "data/processed/weather_observations"
)

spark.stop()