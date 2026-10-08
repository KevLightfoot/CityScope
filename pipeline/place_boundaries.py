"""
place_boundaries.py converts processed Census place geometries
into GeoJSON for use by the CityScope frontend
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

# Create Spark session
spark = (
    SparkSession.builder
    .appName("CityScope Place Boundaries")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.7.0-28.5"
    )
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Initialize Sedona
from sedona.spark import SedonaContext

spark = SedonaContext.create(spark)

# Read processed Census place geometries
places_df = (
    spark.read
    .parquet("data/processed/places")
)

# Convert Sedona geometries to GeoJSON
place_boundaries = (
    places_df
    .select(
        "GEOID",
        "NAME",
        "NAMELSAD",
        expr("ST_AsGeoJSON(geometry)").alias("geojson")
    )
)

# Write browser-friendly boundary data
place_boundaries.write.mode("overwrite").parquet(
    "data/processed/place_boundaries"
)

# Verify output
print("ROWS:", place_boundaries.count())

place_boundaries.filter(
    place_boundaries.GEOID == "4805000"
).select(
    "GEOID",
    "NAME",
    "NAMELSAD",
    "geojson"
).show(1, truncate=100)

spark.stop()