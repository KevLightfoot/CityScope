"""
Create a JSON file containing browser-ready CityScope neighborhood boundaries.
"""

import json

from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Boundaries JSON")
    .config("spark.sql.parquet.enableVectorizedReader", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


neighborhoods = (
    spark.read
    .parquet("data/processed/neighborhood_boundaries")
    .select(
        "nbhd_id",
        "neighborhood",
        "city",
        "state",
        "state_abbr",
        "geojson"
    )
    .collect()
)


results = [
    row.asDict()
    for row in neighborhoods
]


with open(
    "data/processed/neighborhood_boundaries.json",
    "w"
) as f:
    json.dump(results, f)


print("ROWS:", len(results))
print("DONE")


spark.stop()