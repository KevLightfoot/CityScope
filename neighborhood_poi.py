"""
neighborhood_poi.py assigns cleaned POIs to CityScope CDNB
neighborhoods and creates neighborhood-level POI summaries.
"""

import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    expr,
    sum,
    upper,
    trim
)

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


# Read cleaned CDNB neighborhood boundaries.
neighborhood_df = (
    sedona.read.parquet("data/processed/neighborhoods/")
    .select(
        "city", "state", "state_abbr",
        "nbhd_id", "neighborhood", "geometry"
    )
    .cache()
)


# Get the CDNB cities to process.
cities = (
    neighborhood_df
    .select("city", "state", "state_abbr")
    .distinct()
    .orderBy("state_abbr", "city")
    .collect()
)

print(f"Found {len(cities)} CDNB cities.", flush=True)


# Read cleaned POIs once.
poi_df = (
    sedona.read.parquet("data/processed/poi/")
    .select(
        "id", "geometry", "category",
        "cityscope_category", "state"
    )
    .filter(col("geometry").isNotNull())
    .withColumn("geometry", ST_GeomFromWKB(col("geometry")))
    .withColumn("state_abbr", upper(trim(col("state"))))
    .cache()
)

print("POI dataset loaded.", flush=True)


# Define neighborhood POI metrics.
metrics = [
    ("food_count", "cityscope_category = 'food'"),
    ("grocery_count", "cityscope_category = 'grocery'"),
    ("healthcare_count", "cityscope_category = 'healthcare'"),
    ("education_count", "cityscope_category = 'education'"),
    ("shopping_count", "cityscope_category = 'shopping'"),
    ("financial_count", "cityscope_category = 'financial'"),
    ("fitness_count", "cityscope_category = 'fitness'"),
    ("recreation_count", "cityscope_category = 'recreation'"),
    ("entertainment_count", "cityscope_category = 'entertainment'"),
    ("lodging_count", "cityscope_category = 'lodging'"),
    ("religious_count", "cityscope_category = 'religious'"),
    ("restaurant_count", "lower(category) LIKE '%restaurant%'"),
    ("coffee_shop_count", "lower(category) IN ('coffee_shop', 'cafe')"),
    ("grocery_store_count", "lower(category) = 'grocery_store'"),
    ("convenience_store_count", "lower(category) = 'convenience_store'"),
    ("park_count", "lower(category) = 'park'"),
    ("trail_count", "lower(category) = 'trail'"),
    ("gym_count", "lower(category) = 'gym'"),
    ("hospital_count", "lower(category) LIKE '%hospital%'"),
    ("doctors_office_count", "lower(category) LIKE '%doctors_office%'"),
    ("dental_clinic_count", "lower(category) LIKE '%dental%'"),
    ("school_count", "lower(category) LIKE '%school%'"),
    (
        "college_university_count",
        "lower(category) LIKE '%college%' OR "
        "lower(category) LIKE '%university%'"
    ),
    ("museum_count", "lower(category) LIKE '%museum%'"),
    ("gas_station_count", "lower(category) = 'gas_station'")
]


output_path = "data/processed/neighborhood_poi"
total_start = time.time()


# Process each city independently.
for index, city_row in enumerate(cities, start=1):

    city = city_row["city"]
    state_abbr = city_row["state_abbr"]
    city_start = time.time()

    print(
        f"\n[{index}/{len(cities)}] Processing "
        f"{city}, {state_abbr}",
        flush=True
    )


    # Get this city's neighborhoods.
    city_neighborhoods = neighborhood_df.filter(
        (col("city") == city) &
        (col("state_abbr") == state_abbr)
    ).cache()

    neighborhood_count = city_neighborhoods.count()

    print(
        f"Neighborhoods: {neighborhood_count}",
        flush=True
    )


    # Get the city's bounding box.
    bounds = city_neighborhoods.agg(
        expr("min(ST_XMin(geometry))").alias("min_lng"),
        expr("max(ST_XMax(geometry))").alias("max_lng"),
        expr("min(ST_YMin(geometry))").alias("min_lat"),
        expr("max(ST_YMax(geometry))").alias("max_lat")
    ).collect()[0]


    # Keep only POIs inside this city's bounding box.
    city_pois = poi_df.filter(
        (col("state_abbr") == state_abbr) &
        expr(
            f"ST_X(geometry) BETWEEN "
            f"{bounds['min_lng']} AND {bounds['max_lng']}"
        ) &
        expr(
            f"ST_Y(geometry) BETWEEN "
            f"{bounds['min_lat']} AND {bounds['max_lat']}"
        )
    ).cache()

    poi_count = city_pois.count()

    print(
        f"POIs in bounding box: {poi_count:,}",
        flush=True
    )


    # Assign POIs to neighborhoods.
    print("Running spatial join...", flush=True)

    city_matches = (
        city_pois.alias("p")
        .join(
            city_neighborhoods.alias("n"),
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


    # Build all POI metric columns.
    metric_columns = [
        sum(
            expr(f"CASE WHEN {condition} THEN 1 ELSE 0 END")
        ).alias(name)
        for name, condition in metrics
    ]


    # Aggregate POIs by neighborhood.
    poi_aggregated = (
        city_matches
        .groupBy(
            "city",
            "state",
            "state_abbr",
            "nbhd_id",
            "neighborhood"
        )
        .agg(
            count("*").alias("poi_count"),
            *metric_columns
        )
    )


    # Write this city immediately.
    poi_aggregated.write.mode("append").parquet(output_path)

    city_time = time.time() - city_start

    print(
        f"Finished {city}, {state_abbr} "
        f"in {city_time / 60:.1f} minutes.",
        flush=True
    )

    city_pois.unpersist()
    city_neighborhoods.unpersist()


# Finish.
total_time = time.time() - total_start

print(
    f"\nNeighborhood POI pipeline complete in "
    f"{total_time / 60:.1f} minutes.",
    flush=True
)

poi_df.unpersist()
neighborhood_df.unpersist()

spark.stop()