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
        trim(substring(col("value"), 1, 11)).alias("station_id"), 
        trim(substring(col("value"), 13, 8)).cast(DoubleType()).alias("latitude"),
        trim(substring(col("value"), 22, 9)).cast(DoubleType()).alias("longitude"),
        trim(substring(col("value"), 32, 6)).cast(DoubleType()).alias("elevation"),
        trim(substring(col("value"), 42, 30)).alias("station_name")
    )
)

# Join weather_cleaned and stations_df
weather_and_stations = (
    weather_cleaned.join(stations_df, "station_id", "inner")
    )

# Final cleaned weather observations df
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

weather_observations_final.write.mode("overwrite").parquet("data/processed/weather_observations")




# weather_and_stations.filter(col("station_id").startswith("US")).select("station_id", "date", "element", "temperature_f", "latitude", "longitude", "station_name").show(5, truncate=False)






