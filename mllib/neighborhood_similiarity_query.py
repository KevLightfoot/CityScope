"""
neighborhood_similarity_query.py uses saved Spark MLlib vectors and a
similarity model to find neighborhoods similar to a selected neighborhood.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Similarity Query")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read saved neighborhood vectors.
neighborhood_vectors = spark.read.parquet(
    "data/processed/neighborhood_similarity_vectors"
)


# Load the saved MLlib similarity model.
from pyspark.ml.feature import BucketedRandomProjectionLSHModel

lsh_model = BucketedRandomProjectionLSHModel.load(
    "data/processed/neighborhood_similarity_model"
)


# Query neighborhood from command-line arguments.
if len(sys.argv) < 3:
    print(
        "Usage: python neighborhood_similarity_query.py "
        "<city> <neighborhood>",
        flush=True
    )
    spark.stop()
    sys.exit(1)


query_city = sys.argv[1]
query_neighborhood = " ".join(sys.argv[2:])


# Find the requested neighborhood.
query = neighborhood_vectors.filter(
    (col("city") == query_city) &
    (col("nbhd_name") == query_neighborhood)
).limit(1)


if query.count() == 0:
    print(
        f"Neighborhood not found: {query_city}, {query_neighborhood}",
        flush=True
    )
    spark.stop()
    sys.exit(1)


query_row = query.collect()[0]

query_vector = query_row["features"]
query_id = query_row["nbhd_id"]


# Find candidate neighborhoods from the nationwide vector set.
similar_neighborhoods = (
    lsh_model.approxNearestNeighbors(
        neighborhood_vectors,
        query_vector,
        100
    )
)


# Remove the queried neighborhood and invalid names.
similar_neighborhoods = similar_neighborhoods.filter(
    ~(
        (col("city") == query_city) &
        (col("state") == query_row["state"]) &
        (col("nbhd_id") == query_id)
    ) &
    col("nbhd_name").isNotNull() &
    (col("nbhd_name") != "") &
    ~col("nbhd_name").rlike("(?i)https?://") &
    ~col("nbhd_name").rlike("^[0-9]+$") &
    (col("distCol") <= 1.6)
)


# Keep up to three similar neighborhoods from the same city.
same_city = (
    similar_neighborhoods
    .filter(
        (col("city") == query_city) &
        (col("state") == query_row["state"])
    )
    .orderBy("distCol")
    .limit(3)
)


# Keep up to five similar neighborhoods from other cities.
other_cities = (
    similar_neighborhoods
    .filter(
        ~(
            (col("city") == query_city) &
            (col("state") == query_row["state"])
        )
    )
    .orderBy("distCol")
    .limit(5)
)


# Display similar neighborhoods from the same city.
print(
    f"\nSIMILAR {query_city.upper()} NEIGHBORHOODS:",
    flush=True
)

same_city.select(
    "city",
    "state",
    "nbhd_name",
    "nbhd_id",
    "distCol"
).show(
    3,
    False
)


# Display similar neighborhoods from other cities.
print(
    "SIMILAR NEIGHBORHOODS FROM OTHER CITIES:",
    flush=True
)

other_cities.select(
    "city",
    "state",
    "nbhd_name",
    "nbhd_id",
    "distCol"
).show(
    5,
    False
)


spark.stop()