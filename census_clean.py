"""
census_clean.py is the Census preprocessing stage of CityScope. 
It uses PySpark to read the raw 2024 ACS DP05 dataset, 
select the demographic fields needed by the project, 
convert those fields into usable numeric types, 
remove the Census metadata row, 
and save the cleaned result as Parquet for downstream analysis.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr

# Create a local Spark session for processing the 
# Census dataset using 2 local worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope Census Cleaning")
    .master("local[2]")
    .getOrCreate()
)

# Read the raw Census dataset into a Spark DataFrame.
census_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("data/raw/census/ACSDP5Y2024.DP05-Data.csv")
)

# Select the fields needed by CityScope and convert demographic
# values to appropriate numeric data types.
clean_df = (
    census_df
    .select(
        col("GEO_ID"),
        col("NAME"),
        expr("try_cast(DP05_0001E AS BIGINT)").alias("population"),
        expr("try_cast(DP05_0018E AS DOUBLE)").alias("median_age"),
        expr("try_cast(DP05_0105E AS BIGINT)").alias("housing_units")
    )
    # Remove the metadata row included in the Census CSV.
    .filter(col("GEO_ID") != "Geography")
)

# Data cleaning is complete:
# Write the cleaned Census data as Parquet for downstream processing.
clean_df.write.mode("overwrite").parquet("data/processed/census_clean")

spark.stop()