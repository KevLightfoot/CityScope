from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, row_number
from pyspark.sql.window import Window


spark = (
    SparkSession.builder
    .appName("CityScope City Integration")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ============================================================
# CENSUS
# ============================================================

census_df = spark.read.parquet(
    "data/processed/census_clean"
)

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
    .withColumn("place_rank", row_number().over(place_window))
    .filter(col("place_rank") == 1)
    .drop("place_rank")
)


# ============================================================
# HOUSING
# ============================================================

housing_df = (
    spark.read.parquet("data/processed/housing_city")
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


# ============================================================
# CRIME
# ============================================================

crime_df = (
    spark.read.parquet("data/processed/crime_city")
    .select(
        "city_key",
        "state_key",
        "incident_count"
    )
)


# ============================================================
# WEATHER
# ============================================================

weather_df = (
    spark.read.parquet("data/processed/weather_city")
    .select(
        "place_GEOID",
        "avg_temp",
        "avg_low",
        "avg_high",
        "recorded_high",
        "recorded_low",
        "months_available"
    )
)


# ============================================================
# POI
# ============================================================

poi_df = (
    spark.read.parquet("data/processed/poi_city")
    .drop("state")
)


# ============================================================
# COORDINATES
# ============================================================

coordinates_df = (
    spark.read.parquet("data/processed/place_coordinates")
    .select(
        "place_GEOID",
        "longitude",
        "latitude"
    )
)


# ============================================================
# JOIN CENSUS + HOUSING
# ============================================================

cityscope = (
    census_df
    .join(
        housing_df,
        ["city_key", "state_key"],
        "inner"
    )
)


# ============================================================
# ADD CRIME
# ============================================================

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


# ============================================================
# CREATE PLACE GEOID
# ============================================================

cityscope = (
    cityscope
    .withColumn(
        "place_GEOID",
        col("GEO_ID").substr(10, 7)
    )
)


# ============================================================
# ADD WEATHER
# ============================================================

cityscope = (
    cityscope
    .join(
        weather_df,
        "place_GEOID",
        "left"
    )
)


# ============================================================
# ADD POI
# ============================================================

cityscope = (
    cityscope
    .join(
        poi_df,
        "place_GEOID",
        "left"
    )
)


# ============================================================
# ADD COORDINATES
# ============================================================

cityscope = (
    cityscope
    .join(
        coordinates_df,
        "place_GEOID",
        "left"
    )
)


# ============================================================
# FINAL CLEANUP
# ============================================================

# Keep every real column produced by the pipeline.
# This avoids hardcoding Census column names that may change.

keep_columns = [
    c for c in cityscope.columns
    if c not in {
        "city_name",
        "state",
        "place_name",
        "GEO_ID",
        "NAME"
    }
]

cityscope = cityscope.select(
    col("city_name").alias("city"),
    col("state").alias("state"),
    col("GEO_ID").alias("census_geo_id"),
    col("NAME").alias("census_name"),
    *[col(c) for c in keep_columns]
)


# ============================================================
# WRITE
# ============================================================

cityscope.write.mode("overwrite").parquet(
    "data/processed/cityscope_city"
)


# ============================================================
# VERIFY
# ============================================================

print()
print("========================================")
print("CITYSCOPE CITY DATASET CREATED")
print("========================================")
print("ROWS:", cityscope.count())

print()
print("SAMPLE CITIES:")
cityscope.select(
    "city",
    "state",
    "latitude",
    "longitude"
).show(20, False)

print()
print("COLUMNS:")
print(", ".join(cityscope.columns))


spark.stop()