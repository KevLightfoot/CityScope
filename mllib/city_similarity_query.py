"""
city_similarity_query.py uses saved Spark MLlib vectors and a
similarity model to find cities similar to a selected city.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import BucketedRandomProjectionLSHModel


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope City Similarity Query")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read saved city vectors.
city_vectors = spark.read.parquet(
    "data/processed/city_similarity_vectors"
)


# Load the saved MLlib similarity model.
lsh_model = BucketedRandomProjectionLSHModel.load(
    "data/processed/city_similarity_model"
)


# Query city from command-line arguments.
if len(sys.argv) < 3:
    print(
        "Usage: python city_similarity_query.py <city> <state>",
        flush=True
    )
    spark.stop()
    sys.exit(1)


query_city = sys.argv[1]
query_state = " ".join(sys.argv[2:])


# Find the requested city.
query = city_vectors.filter(
    (col("city") == query_city) &
    (col("state") == query_state)
).limit(1)


if query.count() == 0:
    print(
        f"City not found: {query_city}, {query_state}",
        flush=True
    )
    spark.stop()
    sys.exit(1)


query_row = query.collect()[0]

query_vector = query_row["features"]


# Find candidate cities from the nationwide vector set.
similar_cities = (
    lsh_model.approxNearestNeighbors(
        city_vectors,
        query_vector,
        100
    )
)


# Remove the queried city.
similar_cities = similar_cities.filter(
    ~(
        (col("city") == query_city) &
        (col("state") == query_state)
    )
)


# Apply the similarity threshold.
threshold_matches = (
    similar_cities
    .filter(
        col("distCol") <= 1.6
    )
    .orderBy(
        "distCol"
    )
    .limit(5)
)


# Fall back to the five closest cities if no cities meet the threshold.
if threshold_matches.count() > 0:
    similar_cities = threshold_matches
else:
    similar_cities = (
        similar_cities
        .orderBy("distCol")
        .limit(5)
    )


print(
    f"\nSIMILAR CITIES TO {query_city.upper()}:",
    flush=True
)

similar_cities.select(
    "city",
    "state",
    "distCol"
).show(
    5,
    False
)


spark.stop()