"""
housing_clean.py cleans U.S. real estate data for CityScope using Apache Spark.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring
from sedona.spark import SedonaContext
from sedona.spark.sql.st_constructors import ST_Point
from sedona.spark.sql import ST_Contains

# Create Spark Session
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

# Sedona needed for spatial enrichment
sedona = SedonaContext.create(spark)
spark.sparkContext.setLogLevel("WARN")

# Read nationwide housing data
housing_df = (
    spark.read.parquet("data/raw/housing/national.parquet")
)

# Keep only important fields
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

# Read processed tract data needed for spatial enrichment
tracts = (
    sedona.read
    .format("parquet")
    .load("data/processed/tracts")
    .select(
        "GEOID",
        "geometry"
    )
    .withColumn("state_fips", substring("GEOID", 1, 2))
    .withColumn("county_fips", substring("GEOID", 1, 5))
)

# Filter out null/weird geography fields, non-active/null-priced listings,
# non-residential property types, and extreme priced properties
housing_cleaned = (
    housing_defined.filter(
        col("lat").isNotNull() &
        col("lat").between(-90, 90) &
        col("lng").isNotNull() &
        col("lng").between(-180, 180) &
        (col("status") == "active") &
        (col("list_price") > 0) &
        col("property_type").isin(
            "single_family",
            "condo",
            "townhouse",
            "multi_family",
            "manufactured",
            "apartment"
        ) &
        (col("list_price") <= 3000000) &
        col("county_fips").isNotNull()
    )
    .withColumn("point", ST_Point(col("lng"), col("lat")))
)

# Join housing to matching county tracts before spatial filtering
housing_enriched = (
    housing_cleaned.join(
        tracts,
        housing_cleaned.county_fips == tracts.county_fips,
        "inner"
    )
    .filter(
        ST_Contains(col("geometry"), col("point"))
    )
    .drop(tracts.county_fips)
)

# Final parquet write
housing_enriched.write.mode("overwrite").parquet(
    "data/processed/housing"
)

spark.stop()