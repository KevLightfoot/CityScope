"""
query_cities.py combines the cleaned Census demographic data with
the Census Places spatial data. It joins the datasets using the
city GEOID, calculates the area of each city boundary using
Apache Sedona, and filters the results to show larger cities only.
"""

from sedona.spark import SedonaContext
from pyspark.sql.functions import col, expr

# Create a local Spark session for processing the
# city data using 2 local worker threads.
# Uses SedonaContext to leverage Sedona's spatial functionality
spark = (
    SedonaContext.builder()
    .appName("CityScope City Analysis")
    .master("local[2]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.1_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

# Reduce Spark logging output and create the Sedona context
# used for spatial analysis.
spark.sparkContext.setLogLevel("FATAL")
sedona = SedonaContext.create(spark)

# Load the cleaned census demographic data.
census_df = spark.read.parquet("data/processed/census_clean")

# Load the cleaned Census places spatial data.
places_df = spark.read.parquet("data/processed/places")

# Convert the Census GEO_ID into the 7-digit place GEOID
# used by the spatial places dataset.
# Rename NAME so it does not conflict with the places dataset.
census_city = (
    census_df
    .withColumn("GEOID", expr("substring(GEO_ID, 10, 7)"))
    .withColumnRenamed("NAME", "city_name")
)

# Join the demographic data with the city boundaries
# using the GEOID shared by both datasets.
city_data = census_city.join(places_df, on="GEOID", how="inner")

# Calculate the area of each city boundary in square kilometers
# using Apache Sedona spatial functions.
city_data = city_data.withColumn("area_sq_km",
    expr(
        "ST_Area("
        "ST_Transform(geometry, 'epsg:4269', 'epsg:3857')"
        ") / 1000000"
    )
)

# Find cities with a population greater than 100,000
# and select the demographic and spatial information
# needed for the CityScope analysis.
large_cities = (
    city_data.filter(col("population") > 100000)
    .select(
        "city_name",
        "STUSPS",
        "population",
        "median_age",
        "housing_units",
        "area_sq_km"
    )
    .orderBy(col("population").desc())
)

print("\nCityScope: Cities with population greater than 100,000:")
large_cities.show(20, truncate=False)

spark.stop()