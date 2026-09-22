from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("CityScope Census Test")
    .master("local[2]")
    .getOrCreate()
)

file_path = "data/raw/census/ACSDP5Y2024.DP05-Data.csv"

census_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(file_path)
)

print("CityScope Census test")
print("Number of records:", census_df.count())

print("\nSchema:")
census_df.printSchema()

print("\nFirst five rows:")
census_df.show(5, truncate=False)

spark.stop()