"""
cityscope_city.py

Builds the CityScope city-level analytics dataset by integrating:

    Census demographics
    Housing market statistics
    Crime statistics

The resulting Parquet dataset contains one row per verified
Census-place / housing-city match.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, row_number
from pyspark.sql.window import Window


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope City Integration")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read processed datasets
census_df = spark.read.parquet(
    "data/processed/census_clean"
)

# CityScope currently integrates Texas housing data,
# so restrict Census data to Texas.
census_df = census_df.filter(
    col("state_key") == "texas"
)


# Resolve Census places that share the same city name.
# Prefer incorporated cities/towns over CDPs.
place_priority = (
    when(col("place_type") == "city", 1)
    .when(col("place_type") == "town", 2)
    .when(col("place_type") == "village", 3)
    .when(col("place_type") == "CDP", 4)
    .otherwise(5)
)

place_window = (
    Window
    .partitionBy("city_key", "state_key")
    .orderBy(place_priority)
)

census_df = (
    census_df
    .withColumn(
        "place_rank",
        row_number().over(place_window)
    )
    .filter(col("place_rank") == 1)
    .drop("place_rank")
)

housing_df = (
    spark.read
    .parquet("data/processed/housing_city")
    .select(
        "city_key",
        "state_key",
        "property_count",
        "median_list_price",
        "avg_list_price",
        "median_price_per_sqft",
        "avg_sqft"
    )
)

crime_df = (
    spark.read
    .parquet("data/processed/crime_city")
    .select(
        "city_key",
        "state_key",
        "incident_count"
    )
)

# Integrate Census + Housing
# Only cities represented in BOTH datasets are included.
cityscope = (
    census_df
    .join(
        housing_df,
        ["city_key", "state_key"],
        "inner"
    )
)


# Add Crime
# Left join so a missing crime record does NOT automatically
# become zero incidents.
cityscope = (
    cityscope
    .join(
        crime_df,
        ["city_key", "state_key"],
        "left"
    )
    .withColumn(
        "crime_data_available",
        col("incident_count").isNotNull()
    )
)


# Select final CityScope city-level fields

cityscope = cityscope.select(
    col("city_name").alias("city"),
    col("state").alias("state"),

    # Census identifiers / demographics
    col("GEO_ID").alias("census_geo_id"),
    col("NAME").alias("census_name"),
    col("population"),
    col("median_age"),
    col("under_5_pct"),
    col("age_5_9_pct"),
    col("age_10_14_pct"),
    col("age_15_19_pct"),
    col("age_20_24_pct"),
    col("age_25_34_pct"),
    col("age_35_44_pct"),
    col("age_45_54_pct"),
    col("age_55_59_pct"),
    col("age_60_64_pct"),
    col("age_65_74_pct"),
    col("age_75_84_pct"),
    col("age_85_plus_pct"),
    col("under_18_pct"),
    col("age_18_plus_pct"),
    col("age_21_plus_pct"),
    col("age_62_plus_pct"),
    col("age_65_plus_pct"),
    col("male_pct"),
    col("female_pct"),
    col("sex_ratio"),
    col("white_pct"),
    col("black_pct"),
    col("american_indian_alaska_native_pct"),
    col("asian_pct"),
    col("native_hawaiian_pacific_islander_pct"),
    col("other_race_pct"),
    col("two_or_more_races_pct"),
    col("hispanic_latino_pct"),

    # Housing
    col("property_count"),
    col("median_list_price"),
    col("avg_list_price"),
    col("median_price_per_sqft"),
    col("avg_sqft"),

    # Crime
    col("incident_count"),
    col("crime_data_available")
)


# Write integrated CityScope dataset
cityscope.write.mode("overwrite").parquet("data/processed/cityscope_city")


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

city_count = cityscope.count()

crime_count = (
    cityscope
    .filter(col("crime_data_available"))
    .count()
)

print("\n========================================")
print("CITYSCOPE CITY INTEGRATION COMPLETE")
print("========================================")

print(f"Unique Texas Census places after resolution: {census_df.count()}")
print(f"CityScope city records: {city_count}")
print(f"Cities with crime data: {crime_count}")

if city_count > 0:
    print(
        f"Crime coverage: "
        f"{(crime_count / city_count) * 100:.1f}%"
    )

print("\nSchema:")
cityscope.printSchema()

print("\nLargest cities by population:")
cityscope.orderBy(
    col("population").desc()
).select(
    "city",
    "state",
    "population",
    "median_age",
    "property_count",
    "median_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "incident_count"
).show(15, truncate=False)

# ---------------------------------------------------------
# Stop Spark
# ---------------------------------------------------------

spark.stop()