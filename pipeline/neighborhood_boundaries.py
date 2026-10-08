"""
Create browser-ready GeoJSON boundaries for CityScope neighborhoods.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from sedona.spark import SedonaContext
from sedona.spark.sql import st_functions as st


spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Boundaries")
    .getOrCreate()
)

spark = SedonaContext.create(spark)
spark.sparkContext.setLogLevel("ERROR")


# Read neighborhood boundaries
neighborhoods = (
    spark.read
    .parquet("data/processed/neighborhoods")
)


# Convert Sedona geometry to GeoJSON
result = (
    neighborhoods
    .filter(col("geometry").isNotNull())
    .select(
        "city",
        "state",
        "state_abbr",
        "nbhd_id",
        "neighborhood",
        st.ST_AsGeoJSON(
            st.ST_GeomFromWKB(col("geometry"))
        ).alias("geojson")
    )
)


# Check the output
print("ROWS:", result.count())
result.show(10, False)


# Save browser-ready boundaries
result.write.mode("overwrite").parquet(
    "data/processed/neighborhood_boundaries"
)

print("DONE")