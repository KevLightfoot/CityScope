"""
neighborhood_similarity_query.py uses saved Spark MLlib vectors and a
similarity model to find the three closest neighborhoods in the same city
and the three closest neighborhoods from other cities.
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
query_state = query_row["state"]


similar_neighborhoods = (
    lsh_model.approxNearestNeighbors(
        neighborhood_vectors,
        query_vector,
        100
    )
)


similar_neighborhoods = similar_neighborhoods.filter(
    ~(
        (col("city") == query_city) &
        (col("state") == query_state) &
        (col("nbhd_id") == query_id)
    ) &
    col("nbhd_name").isNotNull() &
    (col("nbhd_name") != "") &
    ~col("nbhd_name").rlike("(?i)https?://") &
    ~col("nbhd_name").rlike("^[0-9]+$")
)


same_city = (
    similar_neighborhoods
    .filter(
        (col("city") == query_city) &
        (col("state") == query_state)
    )
    .orderBy("distCol")
    .limit(3)
)


other_cities = (
    similar_neighborhoods
    .filter(
        ~(
            (col("city") == query_city) &
            (col("state") == query_state)
        )
    )
    .orderBy("distCol")
    .limit(3)
)


# Convert distance into a readable match score out of 10.
# distCol = 0 gives 10/10. Larger distances produce lower scores.
same_city = same_city.withColumn(
    "match_score",
    round(10 / (1 + col("distCol")), 1)
)

other_cities = other_cities.withColumn(
    "match_score",
    round(10 / (1 + col("distCol")), 1)
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