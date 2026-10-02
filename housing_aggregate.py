"""
housing_aggregate.py aggregates cleaned housing listings into
city-level housing summaries for CityScope.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, expr, when, lower, trim

# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope Housing Aggregation")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Read cleaned housing data.
housing_df = (
    spark.read.parquet("data/processed/housing/")
)


# Normalize city and state values for dataset joins.
housing_df = (
    housing_df
    .withColumn(
        "city_key",
        lower(trim(col("city")))
    )
    .withColumn(
        "state_key",
        when(
            lower(trim(col("state"))) == "tx",
            "texas"
        ).otherwise(
            lower(trim(col("state")))
        )
    )
)


# Calculate city-level housing metrics.
housing_aggregated = (
    housing_df
    .groupBy("city", "state", "city_key", "state_key")
    .agg(
        # Number of housing listings in the city.
        count("*").alias("property_count"),

        # Median listing price.
        expr(
            "percentile_approx(list_price, 0.5, 10000)"
        ).alias("median_list_price"),

        # Average listing price.
        avg("list_price").alias("avg_list_price"),

        # Price per square foot.
        expr(
            """
            percentile_approx(
                CASE
                    WHEN sqft > 0 AND list_price > 0
                    THEN list_price / sqft
                END,
                0.5,
                10000
            )
            """
        ).alias("median_price_per_sqft"),

        # Average square footage.
        avg(
            when(col("sqft") > 0, col("sqft"))
        ).alias("avg_sqft"),
    )
)

# Save city-level housing summaries as Parquet.
housing_aggregated.write.mode("overwrite").parquet("data/processed/housing_city")

spark.stop()