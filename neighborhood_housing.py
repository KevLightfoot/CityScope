"""
neighborhood_housing.py assigns cleaned housing listings to
CityScope CDNB neighborhoods and creates neighborhood-level
housing summaries.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, expr, when, trim

from sedona.spark import SedonaContext
from sedona.spark.sql import ST_Contains



# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Housing")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

sedona = SedonaContext.create(spark)


# Read cleaned housing data.
housing_df = (
    spark.read.parquet("data/processed/housing/")
    .select(
        "id",
        "state",
        "lat",
        "lng",
        "list_price",
        "sqft"
    )
    .filter(
        col("lat").isNotNull() &
        col("lng").isNotNull() &
        col("list_price").isNotNull() &
        (col("list_price") > 0)
    )
)


# Read cleaned CDNB neighborhood boundaries.
neighborhood_df = (
    sedona.read.parquet("data/processed/neighborhoods/")
    .select(
        "city",
        "state",
        "state_abbr",
        "nbhd_id",
        "neighborhood",
        "geometry"
    )
)


# Normalize housing state abbreviations.
housing_df = (
    housing_df
    .withColumn(
        "state_abbr",
        trim(col("state"))
    )
)

# Create housing point geometries.
housing_df = (
    housing_df
    .withColumn(
        "point",
        expr("ST_Point(lng, lat)")
    )
)


# Assign each housing listing to a CDNB neighborhood.
housing_neighborhoods = (
    housing_df.alias("h")
    .join(
        neighborhood_df.alias("n"),
        (col("h.state_abbr") == col("n.state_abbr")) &
        ST_Contains(
            col("n.geometry"),
            col("h.point")
        ),
        "inner"
    )
    .select(
        col("n.city"),
        col("n.state"),
        col("n.state_abbr"),
        col("n.nbhd_id"),
        col("n.neighborhood"),
        col("h.list_price"),
        col("h.sqft")
    )
)


# Calculate neighborhood-level housing metrics.
housing_aggregated = (
    housing_neighborhoods
    .groupBy(
        "city",
        "state",
        "state_abbr",
        "nbhd_id",
        "neighborhood"
    )
    .agg(
        # Number of housing listings in the neighborhood.
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
        ).alias("avg_sqft")
    )
)


# Save neighborhood-level housing summaries as Parquet.
housing_aggregated.write.mode("overwrite").parquet(
    "data/processed/neighborhood_housing"
)

spark.stop()