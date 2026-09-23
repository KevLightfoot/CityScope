"""
weather_clean.py cleans NOAA GHCN-Daily temperature observations and station metadata for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, substring, trim, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType



# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder.appName("CityScope Weather Cleaning")
    .master("local[4]")
    .getOrCreate()
)
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
    # Convert valid tenths-of-a-degree Celsius values to Fahrenheit and
    # represent missing measurements as NULL.
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
        trim(substring(col("value"), 13, 8)).cast(DoubleType()).alias("latitude"),
        trim(substring(col("value"), 22, 9)).cast(DoubleType()).alias("longitude"),
        trim(substring(col("value"), 32, 6)).cast(DoubleType()).alias("elevation"),
        trim(substring(col("value"), 42, 30)).alias("station_name")
    )
)

# Join observations with station metadata using the station identifier.
weather_and_stations = (
    weather_cleaned.join(stations_df, "station_id", "inner")
    )

# Keep the fields required for downstream CityScope weather analysis.
weather_observations_final = (
    weather_and_stations.select(
        col("station_id"),
        col("date"),
        col("element"),
        col("value"),
        col("temperature_f"),
        col("latitude"),
        col("longitude"),
        col("elevation"),
        col("station_name")
    )
)

# Save cleaned observations as Parquet for downstream Spark processing.
weather_observations_final.write.mode("overwrite").parquet("data/processed/weather_observations")

spark.stop()





