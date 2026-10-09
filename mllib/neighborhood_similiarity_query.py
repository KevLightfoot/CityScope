"""
Find the three closest neighborhoods in the same city and the three
closest neighborhoods from other cities using the saved MLlib model.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round


spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Similarity Query")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


neighborhood_vectors = spark.read.parquet(
    "data/processed/neighborhood_similarity_vectors"
)


from pyspark.ml.feature import BucketedRandomProjectionLSHModel

lsh_model = BucketedRandomProjectionLSHModel.load(
    "data/processed/neighborhood_similarity_model"
)


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


query = (
    neighborhood_vectors
    .filter(
        (col("city") == query_city) &
        (col("nbhd_name") == query_neighborhood)
    )
    .limit(1)
)


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
query_state = query_row["state"]


valid_names = (
    col("nbhd_name").isNotNull() &
    (col("nbhd_name") != "") &
    (col("nbhd_name").rlike(".{2,}")) &
    ~col("nbhd_name").rlike("(?i)https?://") &
    ~col("nbhd_name").rlike("^[0-9]+$")
)


# Search the query city separately so its neighborhoods cannot get
# pushed out by nationwide candidates.
same_city_candidates = (
    neighborhood_vectors
    .filter(
        (col("city") == query_city) &
        (col("state") == query_state)
    )
    .filter(valid_names)
)


same_city = (
    lsh_model
    .approxNearestNeighbors(
        same_city_candidates,
        query_vector,
        10
    )
    .filter(
        ~(
            (col("nbhd_id") == query_id) &
            (col("nbhd_name") == query_neighborhood)
        )
    )
    .orderBy("distCol")
    .limit(3)
)


# Search the entire dataset separately for neighborhoods outside
# the query city.
other_city_candidates = (
    neighborhood_vectors
    .filter(
        ~(
            (col("city") == query_city) &
            (col("state") == query_state)
        )
    )
    .filter(valid_names)
)


other_cities = (
    lsh_model
    .approxNearestNeighbors(
        other_city_candidates,
        query_vector,
        100
    )
    .orderBy("distCol")
    .limit(3)
)


# Convert distance into a 0-10 similarity score.
# Smaller distance = higher score.
same_city = same_city.withColumn(
    "match_score",
    round(10 * (-col("distCol") / 5).exp(), 1)
)

other_cities = other_cities.withColumn(
    "match_score",
    round(10 * (-col("distCol") / 5).exp(), 1)
)


print(
    f"\nSIMILAR {query_city.upper()} NEIGHBORHOODS:",
    flush=True
)

same_city.select(
    "city",
    "state",
    "nbhd_name",
    "nbhd_id",
    "match_score"
).show(
    3,
    False
)


print(
    "SIMILAR NEIGHBORHOODS FROM OTHER CITIES:",
    flush=True
)

other_cities.select(
    "city",
    "state",
    "nbhd_name",
    "nbhd_id",
    "match_score"
).show(
    3,
    False
)


spark.stop()