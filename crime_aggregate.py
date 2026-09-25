"""
crime_aggregate.py aggregates cleaned NIBRS offense records 
into city-level crime metrics
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count_distinct

spark = (
    SparkSession.builder
    .appName("CityScope Crime Aggregation")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

crime_df = (
    spark.read
    .parquet("data/processed/crime")
)

crime_city = (
    crime_df.groupBy(
        "city_name", "state_abbreviation"
    )
    .agg(
        count_distinct("unique_incident_id")
        .alias("incident_count")
    )
)

crime_city.write.mode("overwrite").parquet(
    "data/processed/crime_city"
)

spark.stop()

