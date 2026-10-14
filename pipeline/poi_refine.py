
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, trim, lower

spark = (
    SparkSession.builder
    .master("local[4]")
    .appName("CityScope_POI_Refine")
    .getOrCreate()
)
"""
# Load POIs
df = spark.read.parquet("data/processed/poi_detail")

# Extract address fields from the first address
df_dupe = df.select(
    col("name"),
    col("addresses")[0]["freeform"].alias("street"),
    col("addresses")[0]["locality"].alias("city"),
    col("addresses")[0]["postcode"].alias("postcode"),
    col("addresses")[0]["region"].alias("state"),
    col("addresses")[0]["country"].alias("country")
)

# Filter out missing street addresses and names
df_dupe = df_dupe.filter(
    col("name").isNotNull()
    & (trim(col("name")) != "")
    & col("street").isNotNull()
    & (trim(col("street")) != "")
)

# Normalize capitalization and whitespace
df_dupe = df_dupe.select(
    lower(trim(col("name"))).alias("name"),
    lower(trim(col("street"))).alias("street"),
    lower(trim(col("city"))).alias("city"),
    trim(col("postcode")).alias("postcode"),
    lower(trim(col("state"))).alias("state"),
    lower(trim(col("country"))).alias("country")
)

# Group by name and complete address
df_dupes = (
    df_dupe
    .groupBy("name", "street", "city", "postcode", "state", "country")
    .agg(count("*").alias("poi_count"))
    .filter(col("poi_count") > 1)
    .orderBy(col("poi_count").desc())
)

df_dupes.show(50, truncate=False)


from pyspark.sql.functions import sum as spark_sum, count, col

# Total POI records in the original dataset
total_pois = spark.read.parquet(
    "data/processed/poi_detail"
).count()

# Number of records represented by duplicate groups
duplicate_group_records = df_dupes.agg(
    spark_sum("poi_count")
).first()[0]

# Number of excess records if retaining one record per group
excess_duplicates = df_dupes.selectExpr(
    "sum(poi_count - 1) AS excess"
).first()["excess"]

print(f"Total POIs: {total_pois:,}")
print(f"Records in duplicate groups: {duplicate_group_records:,}")
print(f"Excess duplicate records: {excess_duplicates:,}")
print(f"Duplicate combinations: {df_dupes.count():,}")
print(f"Excess records as % of dataset: {excess_duplicates / total_pois * 100:.3f}%")


print("Duplicate combinations:", df_dupes.count())

print(
    "Excess duplicate records:",
    df_dupes.selectExpr("sum(poi_count - 1)").first()[0]
)

spark.stop()
"""


from pyspark.sql.functions import col

df = spark.read.parquet("data/processed/poi_detail")

total = df.count()
print(f"Total POIs: {total:,}\n")

for threshold in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]:
    retained = df.filter(
        col("confidence") >= threshold
    ).count()

    print(
        f"Threshold {threshold:.2f}: "
        f"{retained:,} retained "
        f"({retained / total * 100:.2f}%)"
    )

