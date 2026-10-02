"""
weather_clean.py cleans NOAA GHCN-Daily temperature observations and station metadata for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, substring, trim, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from sedona.spark import SedonaContext
from sedona.spark.sql.st_constructors import ST_Point
from sedona.spark.sql import ST_Contains


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

# Join observations with station metadata using the station identifier.
weather_and_stations = (
    weather_cleaned.join(stations_df, "station_id", "inner")
    )

# Read proccessed tract data needed for spatial enrichment
tracts = (
    sedona.read
    .format("parquet")
    .load("data/processed/tracts")
    .select(
        "GEOID",
        "geometry" 
    )
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

# Keep the fields required for downstream CityScope weather analysis.
weather_observations_final = (
    weather_and_stations.select(
        col("station_id"),
        col("date"),
        col("element"),
        col("value"),
        col("temperature_f"),
        col("lat"),
        col("lng"),
        col("elevation"),
        col("station_name")
    )
    .withColumn("point", ST_Point(col("lng"),  col("lat")))
)

# Spatially enrich weather observations with Census tract and place boundaries.
weather_enriched = (
    weather_observations_final
    .join(
        tracts.alias("tract"),
        ST_Contains(
            col("tract.geometry"),
            col("point")
        ),
        "inner"
    )
    .select(
        weather_observations_final["*"],
        col("tract.GEOID").alias("tract_GEOID")
    )
    .join(
        places.alias("place"),
        ST_Contains(
            col("place.geometry"),
            col("point")
        ),
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
        col("tract_GEOID"),
        col("place.GEOID").alias("place_GEOID"),
        col("place.NAME").alias("place_name")
    )
)


# Final parquet write
weather_enriched.write.mode("overwrite").parquet("data/processed/weather_observations")

spark.stop()





