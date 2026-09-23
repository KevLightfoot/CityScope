"""
weather_clean.py processes NOAA GHCN-Daily observations for Spark for CityScope
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, substring, trim
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType



# Create Spark Session
spark = (
    SparkSession.builder.appName("CityScope Weather Cleaning")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Create NOAA Observation Schema 
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

# Read compressed CSV using weather_schema
# and create a DF
weather_df = (
    spark.read
    .option("header", "False")
    .schema(weather_schema)
    .option("sep", ",")
    .option("compression", "gzip")
    .csv("data/raw/weather/2022.csv.gz")

)

# Clean weather_df to include only US Stations, temperature in fahrenheit, and formatted date
weather_cleaned = (
    weather_df
    .filter(
        col("station_id").startswith("US")
        &
        col("element").isin("TAVG","TMAX","TMIN")
    )
    .withColumn("temperature_f", ((col("value") / 10.0) * 9/5) + 32)
    .withColumn("date", to_date(col("date"), "yyyyMMdd"))
)

# read metadata from each station for stations_df construction
stations_raw = (
    spark.read.text("data/raw/weather/ghcnd-stations.txt")
)

# Create DF for weather stations 
stations_df = (
    stations_raw.select(
        substring(col("value"), 1, 11).trim().alias("station_id"), 
        substring(col("value"), 13, 8).trim().cast(DoubleType()).alias("latitude"),
        substring(col("value"), 22, 9).trim().cast(DoubleType()).alias("longitude"),
        substring(col("value"), 32, 6).trim().cast(DoubleType()).alias("elevation"),
        substring(col("value"), 42, 30).trim().alias("sation_name")
    )
)

stations_df.filter(col("station_id").startswith("US")).show(5, truncate=False)






