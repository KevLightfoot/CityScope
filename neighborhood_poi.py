"""
neighborhood_poi.py assigns cleaned POIs to CityScope CDNB
neighborhoods and creates neighborhood-level POI summaries.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, expr, sum, upper, trim, broadcast

from sedona.spark import SedonaContext
from sedona.spark.sql import ST_Contains, ST_GeomFromWKB


# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood POI")
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


# Read cleaned POI data.
# Read cleaned POI data.
poi_df = (
    sedona.read.parquet("data/processed/poi/")
    .select(
        "id",
        "geometry",
        "category",
        "cityscope_category",
        "state"
    )
    .filter(
        col("geometry").isNotNull()
    )
    .withColumn(
        "geometry",
        ST_GeomFromWKB(col("geometry"))
    )
    .withColumn(
        "state_abbr",
        upper(trim(col("state")))
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
    .cache()
)


# Create city-level bounding boxes from CDNB neighborhoods.
city_bounds = (
    neighborhood_df
    .groupBy(
        "city",
        "state",
        "state_abbr"
    )
    .agg(
        expr("min(ST_XMin(geometry))").alias("min_lng"),
        expr("max(ST_XMax(geometry))").alias("max_lng"),
        expr("min(ST_YMin(geometry))").alias("min_lat"),
        expr("max(ST_YMax(geometry))").alias("max_lat")
    )
)


# Keep only POIs inside CDNB city bounding boxes.
poi_candidates = (
    poi_df.alias("p")
    .join(
        broadcast(city_bounds).alias("c"),
        (col("p.state_abbr") == col("c.state_abbr")) &
        (expr("ST_X(p.geometry)") >= col("c.min_lng")) &
        (expr("ST_X(p.geometry)") <= col("c.max_lng")) &
        (expr("ST_Y(p.geometry)") >= col("c.min_lat")) &
        (expr("ST_Y(p.geometry)") <= col("c.max_lat")),
        "inner"
    )
    .select(
        col("p.id"),
        col("p.geometry"),
        col("p.category"),
        col("p.cityscope_category"),
        col("p.state_abbr"),
        col("c.city").alias("candidate_city")
    )
)


# Assign POIs to their actual CDNB neighborhoods.
poi_neighborhoods = (
    poi_candidates.alias("p")
    .join(
        neighborhood_df.alias("n"),
        (col("p.state_abbr") == col("n.state_abbr")) &
        (col("p.candidate_city") == col("n.city")) &
        ST_Contains(
            col("n.geometry"),
            col("p.geometry")
        ),
        "inner"
    )
    .select(
        col("n.city"),
        col("n.state"),
        col("n.state_abbr"),
        col("n.nbhd_id"),
        col("n.neighborhood"),
        col("p.category"),
        col("p.cityscope_category")
    )
)


# Calculate neighborhood-level POI metrics.
poi_aggregated = (
    poi_neighborhoods
    .groupBy(
        "city",
        "state",
        "state_abbr",
        "nbhd_id",
        "neighborhood"
    )
    .agg(
        count("*").alias("poi_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'food' "
            "THEN 1 ELSE 0 END"
        )).alias("food_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'grocery' "
            "THEN 1 ELSE 0 END"
        )).alias("grocery_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'healthcare' "
            "THEN 1 ELSE 0 END"
        )).alias("healthcare_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'education' "
            "THEN 1 ELSE 0 END"
        )).alias("education_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'shopping' "
            "THEN 1 ELSE 0 END"
        )).alias("shopping_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'financial' "
            "THEN 1 ELSE 0 END"
        )).alias("financial_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'fitness' "
            "THEN 1 ELSE 0 END"
        )).alias("fitness_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'recreation' "
            "THEN 1 ELSE 0 END"
        )).alias("recreation_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'entertainment' "
            "THEN 1 ELSE 0 END"
        )).alias("entertainment_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'lodging' "
            "THEN 1 ELSE 0 END"
        )).alias("lodging_count"),

        sum(expr(
            "CASE WHEN cityscope_category = 'religious' "
            "THEN 1 ELSE 0 END"
        )).alias("religious_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%restaurant%' "
            "THEN 1 ELSE 0 END"
        )).alias("restaurant_count"),

        sum(expr(
            "CASE WHEN lower(category) IN ('coffee_shop', 'cafe') "
            "THEN 1 ELSE 0 END"
        )).alias("coffee_shop_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'grocery_store' "
            "THEN 1 ELSE 0 END"
        )).alias("grocery_store_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'convenience_store' "
            "THEN 1 ELSE 0 END"
        )).alias("convenience_store_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'park' "
            "THEN 1 ELSE 0 END"
        )).alias("park_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'trail' "
            "THEN 1 ELSE 0 END"
        )).alias("trail_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'gym' "
            "THEN 1 ELSE 0 END"
        )).alias("gym_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%hospital%' "
            "THEN 1 ELSE 0 END"
        )).alias("hospital_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%doctors_office%' "
            "THEN 1 ELSE 0 END"
        )).alias("doctors_office_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%dental%' "
            "THEN 1 ELSE 0 END"
        )).alias("dental_clinic_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%school%' "
            "THEN 1 ELSE 0 END"
        )).alias("school_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%college%' OR "
            "lower(category) LIKE '%university%' "
            "THEN 1 ELSE 0 END"
        )).alias("college_university_count"),

        sum(expr(
            "CASE WHEN lower(category) LIKE '%museum%' "
            "THEN 1 ELSE 0 END"
        )).alias("museum_count"),

        sum(expr(
            "CASE WHEN lower(category) = 'gas_station' "
            "THEN 1 ELSE 0 END"
        )).alias("gas_station_count")
    )
)


# Save neighborhood-level POI summaries as Parquet.
poi_aggregated.write.mode("overwrite").parquet(
    "data/processed/neighborhood_poi"
)

spark.stop()