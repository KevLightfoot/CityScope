"""
tract_clean.py takes nationwide Census tract boundaries from a Census shapefile,
loads them using Apache Sedona,
keeps the geographic information CityScope needs,
and saves the result in Parquet so the tract data can be used efficiently later.
"""

from sedona.spark import SedonaContext

# Create a local Spark session for processing the 
# spatial data using 4 local worker threads.
# Uses SedonaContext to leverage Sedona's spatial functionality
spark = (
    SedonaContext.builder()
    .appName("CityScope Tract Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

sedona = SedonaContext.create(spark)


tracts_df = (
    sedona.read
    .format("shapefile")
    .load("data/raw/spatial/tracts/cb_2024_us_tract_500k.shp")
    .select(
        "GEOID",
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "STUSPS",
        "STATE_NAME",
        "NAMELSAD",
        "ALAND",
        "AWATER",
        "geometry",
    )
)

tracts_df.write.mode("overwrite").parquet("data/processed/tracts")


