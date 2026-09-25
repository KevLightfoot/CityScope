"""
housing_clean.py cleans U.S. real estate data for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from sedona.spark import SedonaContext
from sedona.spark.sql.st_constructors import ST_Point
from sedona.spark.sql import ST_Contains



spark = (
    SedonaContext.builder()
    .appName("Cityscope Housing Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

sedona = SedonaContext.create(spark)
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

tracts = (
    sedona.read
    .format("parquet")
    .load("data/processed/tracts")
    .select(
        "GEOID",
        "geometry" 
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
    .withColumn("point", ST_Point(col("lng"), col("lat")))
)

housing_enriched = (
    housing_cleaned.join(tracts, ST_Contains(tracts.geometry, housing_cleaned.point), "inner")
)

# housing_cleaned.write.mode("overwrite").parquet("data/processed/housing_clean")
housing_enriched.select("lat", "lng", "GEOID").show(20, truncate = False)

print("Cleaned:", housing_cleaned.count())
print("Enriched:", housing_enriched.count())

unmatched = housing_cleaned.join(
    housing_enriched.select("id").distinct(),
    "id",
    "left_anti"
)

spark.stop()