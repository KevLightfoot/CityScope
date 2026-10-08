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
        "place_name",
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
# BUILD CITY DATASET
# ============================================================

cityscope = (
    census_df
    .join(
        housing_df,
        ["city_key", "state_key"],
        "inner"
    )
)

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


# Census GEO_ID looks like:
# 0500000US4805000
#
# The last 7 digits are the Census place GEOID.

cityscope = (
    cityscope
    .withColumn(
        "place_GEOID",
        col("GEO_ID").substr(10, 7)
    )
)


cityscope = (
    cityscope
    .join(
        weather_df,
        "place_GEOID",
        "left"
    )
)

cityscope = (
    cityscope
    .join(
        poi_df,
        "place_GEOID",
        "left"
    )
)

cityscope = (
    cityscope
    .join(
        coordinates_df,
        "place_GEOID",
        "left"
    )
)


# ============================================================
# FINAL DATASET
# ============================================================

cityscope = cityscope.select(
    col("city_name").alias("city"),
    col("state").alias("state"),

    col("GEO_ID").alias("census_geo_id"),
    col("NAME").alias("census_name"),

    col("population"),
    col("median_age"),
    col("median_household_income"),
    col("per_capita_income"),
    col("poverty_rate"),
    col("bachelors_degree_pct"),
    col("graduate_degree_pct"),
    col("unemployment_rate"),
    col("labor_force"),
    col("avg_household_size"),

    col("white_pct"),
    col("black_pct"),
    col("asian_pct"),
    col("american_indian_pct"),
    col("native_hawaiian_pct"),
    col("other_race_pct"),
    col("two_or_more_races_pct"),
    col("hispanic_pct"),

    col("age_under_5_pct"),
    col("age_5_17_pct"),
    col("age_18_24_pct"),
    col("age_25_34_pct"),
    col("age_35_44_pct"),
    col("age_45_54_pct"),
    col("age_55_64_pct"),
    col("age_65_74_pct"),
    col("age_75_84_pct"),
    col("age_85_plus_pct"),

    col("property_count"),
    col("median_list_price"),
    col("avg_list_price"),
    col("median_price_per_sqft"),
    col("avg_sqft"),

    col("incident_count"),
    col("crime_data_available"),

    col("avg_temp"),
    col("avg_low"),
    col("avg_high"),
    col("recorded_high"),
    col("recorded_low"),
    col("months_available"),

    col("place_GEOID"),

    col("longitude"),
    col("latitude")
)


# ============================================================
# WRITE
# ============================================================

cityscope.write.mode("overwrite").parquet(
    "data/processed/cityscope_city"
)

print("CITYSCOPE CITY DATASET CREATED")
print("ROWS:", cityscope.count())

cityscope.select(
    "city",
    "state",
    "latitude",
    "longitude"
).show(20, False)

spark.stop()