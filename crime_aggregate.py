"""
crime_aggregate.py aggregates cleaned NIBRS offense records 
into city-level crime metrics
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count_distinct, lower, trim

# Create Spark session
spark = (
    SparkSession.builder
    .appName("CityScope Crime Aggregation")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Read processed crime data
crime_df = (
    spark.read
    .parquet("data/processed/crime")
)

# Normalize city and state values for cross-dataset joins.
crime_df = (
    crime_df
    .withColumn(
        "city_key",
        lower(trim(col("city_name")))
    )
    .withColumn(
        "state_key",
        lower(trim(col("state_abbreviation")))
    )
)

# Group by city and state
# and aggregate by unique incidents
crime_city = (
    crime_df.groupBy(
        "city_name", "state_abbreviation", "city_key", "state_key"
    )
    .agg(
        count_distinct("unique_incident_id")
        .alias("incident_count")
    )
)

# Write finalized parquet
crime_city.write.mode("overwrite").parquet(
    "data/processed/crime_city"
)

spark.stop()