"""
spatial_clean.py takes geographic city/place boundaries from a Census shapefile, 
loads them using Apache Sedona, 
keeps the geographic information CityScope needs, 
and saves the result in Parquet so the spatial data can be used efficiently later.
"""

from sedona.spark import SedonaContext

# Create a local Spark session for processing the 
# spatial data using 2 local worker threads.
# Uses SedonaContext to leverage Sedona's spatial functionality
spark = (
    SedonaContext.builder()
    .appName("CityScope Spatial Clean")
    .master("local[2]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.1_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

# Reduce Spark's logging output 
# and create SedonaContext used to read spatial data
spark.sparkContext.setLogLevel("FATAL")
sedona = SedonaContext.create(spark)

# Read the Census Places shapefile using Apache Sedona 
# and turn it into a Spark DataFrame
places_df = (
    sedona.read
    .format("shapefile")
    .load("data/raw/spatial/cb_2024_us_place_500k.shp")
)

# Keep only the fields needed for CityScope spatial analysis.
# City name, state abbreviation, geographic identifier, and geographic boundaries
places_clean = places_df.select(
    "NAME",
    "STUSPS",
    "GEOID",
    "geometry"
)

# Save the cleaned spatial data as Parquet for downstream processing.
places_clean.write.mode("overwrite").parquet("data/processed/places")

spark.stop()