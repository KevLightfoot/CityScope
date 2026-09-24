"""
housing_clean.py cleans U.S. real estate data for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col


spark = (
    SparkSession.builder.appName("Cityscope Housing Cleaning")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

housing_df = (spark.read.parquet("data/raw/housing/texas_properties.parquet"))

housing_defined = (
    housing_df.select(
        "id",
        "street",
        "unit",
        "city",
        "state",
        "zip",
        "lat",
        "lng",
        "property_type",
        "beds",
        "baths",
        "sqft",
        "lot_sqft",  
        "year_built",
        "status",
        "list_price",
        "county_fips"
    )
)

housing_cleaned = (
    housing_defined.filter(
        col("lat").isNotNull() &
        col("lat").between(-90, 90) &
        col("lng").isNotNull() &
        col("lng").between(-180, 180) &
        (col("status") == "active") &
        (col("list_price") > 0) &
        col("property_type").isin("single_family", "condo", "townhouse", "multi_family", "manufactured", "apartment") &
        (col("list_price") <= 3000000)
    )
)

housing_cleaned.write.mode("overwrite").parquet("data/processed/housing_clean")