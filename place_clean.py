"""
place_clean.py cleans the 2024 Texas Census place boundaries
for use in CityScope spatial analysis.
"""

from sedona.spark import SedonaContext

# Create Spark
spark = (
    SedonaContext.builder()
    .appName("CityScope Place Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)
sedona = SedonaContext.create(spark)

# Read raw data and keep important fields
places_df = (
    sedona.read
    .format("shapefile")
    .load("data/raw/spatial/places/tl_2024_48_place.shp")
    .select(
        "GEOID",
        "NAME",
        "NAMELSAD",
        "LSAD",
        "geometry"
    )
)

#write cleaned parquet
places_df.write.mode("overwrite").parquet(
    "data/processed/places"
)

spark.stop()