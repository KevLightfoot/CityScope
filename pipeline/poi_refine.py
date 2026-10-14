
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, trim, lower

spark = (
    SparkSession.builder
    .master("local[4]")
    .appName("CityScope_POI_Refine")
    .getOrCreate()
)

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

print("Duplicate combinations:", df_dupes.count())

print(
    "Excess duplicate records:",
    df_dupes.selectExpr("sum(poi_count - 1)").first()[0]
)

spark.stop()
