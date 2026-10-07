"""
neighborhood_agg.py takes the results of the 3 neighborhood-level 
metrics and combines them into one parquett file
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, coalesce, lit

spark = SparkSession.builder.master("local[2]").getOrCreate()

BASE = "data/processed"

# Read existing neighborhood datasets
demo = spark.read.parquet(
    f"{BASE}/neighborhood_demographics"
)

housing = spark.read.parquet(
    f"{BASE}/neighborhood_housing"
)

poi = spark.read.parquet(
    f"{BASE}/neighborhood_poi"
)

neighborhoods = spark.read.parquet(
    f"{BASE}/neighborhoods"
)

keys = [
    "city",
    "state",
    "state_abbr",
    "nbhd_id"
]

print("=" * 70)
print("INPUT DATASETS")
print("=" * 70)

print("DEMOGRAPHICS:", demo.count())
print("HOUSING:", housing.count())
print("POI:", poi.count())

# Demographics
demo_cols = [
    "city",
    "state",
    "state_abbr",
    "nbhd_id",
    "pop",
    "pop_white",
    "pop_black",
    "pop_hisp",
    "pop_aian",
    "pop_asian",
    "pop_nhpi",
    "pop_other",
    "pop_two",
    "white_pct",
    "black_pct",
    "hisp_pct",
    "aian_pct",
    "asian_pct",
    "nhpi_pct",
    "other_pct",
    "two_pct"
]

demo = demo.select(*demo_cols)

# Housing
housing_cols = [
    "property_count",
    "median_list_price",
    "avg_list_price",
    "median_price_per_sqft",
    "avg_sqft"
]

available_housing_cols = [
    c for c in housing_cols
    if c in housing.columns
]

housing = housing.select(
    *keys,
    *available_housing_cols
)

# POI
poi_cols = [
    "poi_count",
    "food_count",
    "grocery_count",
    "healthcare_count",
    "education_count",
    "shopping_count",
    "financial_count",
    "fitness_count",
    "recreation_count",
    "entertainment_count",
    "lodging_count",
    "religious_count",
    "restaurant_count",
    "coffee_shop_count",
    "grocery_store_count",
    "convenience_store_count",
    "park_count",
    "trail_count",
    "gym_count",
    "hospital_count",
    "doctors_office_count",
    "dental_clinic_count",
    "school_count",
    "college_university_count",
    "museum_count",
    "gas_station_count"
]

available_poi_cols = [
    c for c in poi_cols
    if c in poi.columns
]

poi = poi.select(
    *keys,
    *available_poi_cols
)

# Neighborhood names
neighborhood_names = neighborhoods.select(
    *keys,
    col("neighborhood").alias("nbhd_name")
).dropDuplicates(keys)

# Join
print("\n" + "=" * 70)
print("BUILDING NEIGHBORHOOD AGGREGATE")
print("=" * 70)

combined = (
    demo
    .join(
        housing,
        keys,
        "left"
    )
    .join(
        poi,
        keys,
        "left"
    )
    .join(
        neighborhood_names,
        keys,
        "left"
    )
)

# Fill missing POI counts with 0

for c in available_poi_cols:
    combined = combined.withColumn(
        c,
        coalesce(col(c), lit(0))
    )

# VEerification
print("\n" + "=" * 70)
print("OUTPUT VERIFICATION")
print("=" * 70)

print("ROWS:", combined.count())
print("COLUMNS:", len(combined.columns))

print(
    "DUPLICATE KEYS:",
    combined.groupBy(*keys)
            .count()
            .filter(col("count") > 1)
            .count()
)

print(
    "NULL NBHD IDS:",
    combined.filter(col("nbhd_id").isNull()).count()
)

print(
    "NULL NAMES:",
    combined.filter(col("nbhd_name").isNull()).count()
)

print(
    "CITIES:",
    combined.select("city").distinct().count()
)

print(
    "STATES:",
    combined.select("state").distinct().count()
)

# Austin Check
print("\nAUSTIN")

austin = combined.filter(
    (col("city") == "Austin") &
    (col("state") == "Texas")
)

print("ROWS:", austin.count())

austin.select(
    "nbhd_id",
    "nbhd_name",
    "pop",
    "property_count",
    "median_list_price",
    "avg_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "poi_count"
).orderBy("nbhd_id").show(15, False)

# New York check
print("\nNEW YORK")

ny = combined.filter(
    col("city") == "NewYork"
)

print("ROWS:", ny.count())

ny.select(
    "nbhd_id",
    "nbhd_name",
    "pop",
    "property_count",
    "median_list_price",
    "poi_count"
).orderBy("nbhd_id").show(10, False)

# Write final aggregated parquett
output = f"{BASE}/neighborhood_cityscope"

print("\nWRITING:", output)

combined.write.mode("overwrite").parquet(output)

print("\n" + "=" * 70)
print("NEIGHBORHOOD AGGREGATE COMPLETE")
print("=" * 70)

spark.stop()