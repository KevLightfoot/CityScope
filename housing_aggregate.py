"""
housing_aggregate.py aggregates cleaned housing listings into
city-level housing summaries for CityScope.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, expr, when


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


# Calculate city-level housing metrics.
housing_aggregated = (
    housing_df
    .groupBy("city", "state")
    .agg(
        # Number of housing listings in the city.
        count("*").alias("property_count"),

        # Median listing price.
        expr(
            "percentile_approx(list_price, 0.5, 10000)"
        ).alias("median_list_price"),

        # Average listing price.
        avg("list_price").alias("avg_list_price"),

        # Median price per square foot.
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


# Display validation information.
print("Housing aggregation complete.")
print(f"City/state records: {housing_aggregated.count()}")

print("\nSchema:")
housing_aggregated.printSchema()

print("\nSample:")
housing_aggregated.orderBy(
    col("property_count").desc()
).show(10, truncate=False)


spark.stop()