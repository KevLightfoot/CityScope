from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("CityScope Parquet Verification")
    .master("local[2]")
    .getOrCreate()
)

parquet_df = spark.read.parquet("data/processed/census_clean")

print("Records loaded from Parquet:", parquet_df.count())

print("\nSchema:")
parquet_df.printSchema()

print("\nSample records:")
parquet_df.show(10, truncate=False)

spark.stop()