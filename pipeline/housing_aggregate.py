"""
housing_aggregate.py aggregates cleaned housing listings into
city-level housing summaries and city-indexed property data
for CityScope.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, expr, when, lower, trim, create_map, lit

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
    spark.read.parquet("data/processed/housing")
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
        create_map(
            lit("al"), lit("alabama"),
            lit("ak"), lit("alaska"),
            lit("az"), lit("arizona"),
            lit("ar"), lit("arkansas"),
            lit("ca"), lit("california"),
            lit("co"), lit("colorado"),
            lit("ct"), lit("connecticut"),
            lit("de"), lit("delaware"),
            lit("dc"), lit("district of columbia"),
            lit("fl"), lit("florida"),
            lit("ga"), lit("georgia"),
            lit("hi"), lit("hawaii"),
            lit("id"), lit("idaho"),
            lit("il"), lit("illinois"),
            lit("in"), lit("indiana"),
            lit("ia"), lit("iowa"),
            lit("ks"), lit("kansas"),
            lit("ky"), lit("kentucky"),
            lit("la"), lit("louisiana"),
            lit("me"), lit("maine"),
            lit("md"), lit("maryland"),
            lit("ma"), lit("massachusetts"),
            lit("mi"), lit("michigan"),
            lit("mn"), lit("minnesota"),
            lit("ms"), lit("mississippi"),
            lit("mo"), lit("missouri"),
            lit("mt"), lit("montana"),
            lit("ne"), lit("nebraska"),
            lit("nv"), lit("nevada"),
            lit("nh"), lit("new hampshire"),
            lit("nj"), lit("new jersey"),
            lit("nm"), lit("new mexico"),
            lit("ny"), lit("new york"),
            lit("nc"), lit("north carolina"),
            lit("nd"), lit("north dakota"),
            lit("oh"), lit("ohio"),
            lit("ok"), lit("oklahoma"),
            lit("or"), lit("oregon"),
            lit("pa"), lit("pennsylvania"),
            lit("ri"), lit("rhode island"),
            lit("sc"), lit("south carolina"),
            lit("sd"), lit("south dakota"),
            lit("tn"), lit("tennessee"),
            lit("tx"), lit("texas"),
            lit("ut"), lit("utah"),
            lit("vt"), lit("vermont"),
            lit("va"), lit("virginia"),
            lit("wa"), lit("washington"),
            lit("wv"), lit("west virginia"),
            lit("wi"), lit("wisconsin"),
            lit("wy"), lit("wyoming")
        )[lower(trim(col("state")))]
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
housing_aggregated.write \
    .mode("overwrite") \
    .parquet("data/processed/housing_city")


# Prepare individual properties for map plotting.
#
# Keep the useful listing information rather than reducing the
# records to only the fields currently displayed by the frontend.
housing_properties = (
    housing_df
    .select(
        "id",
        "street",
        "unit",
        "city",
        "state",
        "zip",
        "lat",
        "lng",
        "property_type",
        "beds",
        "baths",
        "sqft",
        "lot_sqft",
        "year_built",
        "status",
        "list_price",
        "county_fips",
        "city_key",
        "state_key"
    )
    .filter(
        col("lat").isNotNull() &
        col("lng").isNotNull()
    )
)


# Save individual properties partitioned by state and city.
#
# This allows the API to retrieve only the selected city's
# properties instead of scanning the entire housing dataset.
housing_properties.write \
    .mode("overwrite") \
    .partitionBy("state_key", "city_key") \
    .parquet("data/processed/housing_city_properties")


spark.stop()