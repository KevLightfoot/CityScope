from pyspark.sql import SparkSession
from pyspark.sql.functions import col


spark = (
    SparkSession.builder
    .master("local[4]")
    .appName("CityScope_POI_Refine")
    .getOrCreate()
)

df = spark.read.parquet("data/processed/poi_detail")
df.select("name", "addresses").show(30, truncate=False)
"""
df_dupe = (
    spark.read.parquet("data/processed/poi_detail")
    .select(
        col("addresses"),
        col("name")
    )
)


from pyspark.sql.functions import col, count

# Group POIs by name and address, then count duplicates
df_dupes = (
    df_dupe
    .groupBy("name", "addresses")
    .agg(count("*").alias("poi_count"))
    .filter(col("poi_count") > 1)
    .orderBy(col("poi_count").desc())
)

# Show duplicate combinations
df_dupes.show(50, truncate=False)

# Count how many distinct name/address combinations are duplicated
print("Duplicate name/address combinations:", df_dupes.count())

"""