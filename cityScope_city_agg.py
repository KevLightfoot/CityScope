"""
cityScope_city_agg.py builds the CityScope city-level analytics dataset by integrating:
Census demographics and employment
Housing market statistics
Crime statistics
Weather statistics
POI statistics
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
# Census data is now nationwide.
census_df = spark.read.parquet(
    "data/processed/census_clean"
)


# Some Census places share the same city name.
# Prefer cities/towns over CDPs.
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

# Rank Census places by type
census_df = (
    census_df
    .withColumn(
        "place_rank",
        row_number().over(place_window)
    )
    .filter(col("place_rank") == 1)
    .drop("place_rank")
)


# Keep key fields from housing, crime, and weather
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

weather_df = (
    spark.read
    .parquet("data/processed/weather_city")
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

poi_df = (
    spark.read
    .parquet("data/processed/poi_city")
    .drop("state")
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


# Add Weather
# Weather is optional because not every Census place currently
# has a NOAA station assignment.
cityscope = (
    cityscope
    .withColumn(
        "place_GEOID",
        col("GEO_ID").substr(10, 7)
    )
    .join(
        weather_df,
        "place_GEOID",
        "left"
    )
)


# Add POIs
# POI counts are optional because some Census places may have no POIs.
cityscope = (
    cityscope
    .join(
        poi_df,
        "place_GEOID",
        "left"
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

    # Employment / Labor Market
    col("labor_force"),
    col("employed"),
    col("unemployed"),
    col("unemployment_rate"),
    col("management_business_science_arts_pct"),
    col("service_pct"),
    col("sales_office_pct"),
    col("natural_resources_construction_maintenance_pct"),
    col("production_transportation_pct"),

    # Employment by Industry
    col("construction_pct"),
    col("manufacturing_pct"),
    col("retail_pct"),
    col("transportation_utilities_pct"),
    col("information_pct"),
    col("finance_real_estate_pct"),
    col("professional_services_pct"),
    col("education_healthcare_pct"),
    col("arts_accommodation_food_pct"),
    col("public_admin_pct"),

    # Housing
    col("property_count"),
    col("median_list_price"),
    col("avg_list_price"),
    col("median_price_per_sqft"),
    col("avg_sqft"),

    # Crime
    col("incident_count"),
    col("crime_data_available"),

    # Weather
    col("avg_temp"),
    col("avg_low"),
    col("avg_high"),
    col("recorded_high"),
    col("recorded_low"),
    col("months_available"),

    # POIs
    col("poi_food_count"),
    col("poi_grocery_count"),
    col("poi_healthcare_count"),
    col("poi_education_count"),
    col("poi_shopping_count"),
    col("poi_financial_count"),
    col("poi_fitness_count"),
    col("poi_recreation_count"),
    col("poi_entertainment_count"),
    col("poi_transportation_count"),
    col("poi_lodging_count"),
    col("poi_religious_count"),
    col("poi_other_count"),
    col("poi_total_count"),
)


# Write integrated CityScope dataset
cityscope.write.mode("overwrite").parquet(
    "data/processed/cityscope_city"
)

spark.stop()