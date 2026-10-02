"""
cityscope_query.py runs analytical queries on the integrated
CityScope city-level dataset.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col


spark = (
    SparkSession.builder
    .appName("CityScope Analytics")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read integrated CityScope dataset
cityscope = spark.read.parquet(
    "data/processed/cityscope_city"
)


# Example CityScope relocation query:
# Find cities with:
# - population of at least 100,000
# - median listing price <= $400,000
# - available crime data
# - available weather data

results = (
    cityscope
    .filter(col("population") >= 100000)
    .filter(col("median_list_price") <= 400000)
    .filter(col("crime_data_available") == True)
    .filter(col("avg_temp").isNotNull())
    .select(
        "city",
        "state",
        "population",
        "median_list_price",
        "median_price_per_sqft",
        "avg_sqft",
        "incident_count",
        "avg_temp",
        "avg_low",
        "avg_high"
    )
    .orderBy(col("median_list_price").asc())
)


print("CityScope relocation query results:")
results.show(50, truncate=False)


spark.stop()