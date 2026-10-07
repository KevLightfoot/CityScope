"""
neighborhood_mllib.py uses Spark MLlib to identify neighborhoods that are
similar based on demographic, housing, and POI characteristics.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, log1p
from pyspark.ml.feature import VectorAssembler, StandardScaler, Imputer, PCA
from pyspark.ml.feature import BucketedRandomProjectionLSH


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Similarity MLlib")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read integrated CityScope neighborhood-level data.
neighborhood = spark.read.parquet(
    "data/processed/neighborhood_cityscope"
)


# Features used to represent neighborhood characteristics.
model_features = [
    "pop",
    "white_pct",
    "black_pct",
    "hisp_pct",
    "asian_pct",
    "aian_pct",
    "nhpi_pct",
    "other_pct",
    "two_pct",
    "property_count",
    "median_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "poi_count",
    "food_count",
    "grocery_count",
    "healthcare_count",
    "education_count",
    "shopping_count",
    "fitness_count",
    "recreation_count",
    "entertainment_count",
    "restaurant_count",
    "park_count",
    "gym_count",
    "hospital_count",
    "school_count"
]


# Replace missing count values with zero.
neighborhood = neighborhood.fillna(
    0,
    subset=[
        "property_count",
        "poi_count",
        "food_count",
        "grocery_count",
        "healthcare_count",
        "education_count",
        "shopping_count",
        "fitness_count",
        "recreation_count",
        "entertainment_count",
        "restaurant_count",
        "park_count",
        "gym_count",
        "hospital_count",
        "school_count"
    ]
)


# Log-transform highly skewed count and housing features.
log_features = [
    "pop",
    "property_count",
    "median_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "poi_count",
    "food_count",
    "grocery_count",
    "healthcare_count",
    "education_count",
    "shopping_count",
    "fitness_count",
    "recreation_count",
    "entertainment_count",
    "restaurant_count",
    "park_count",
    "gym_count",
    "hospital_count",
    "school_count"
]

for feature in log_features:
    neighborhood = neighborhood.withColumn(
        f"log_{feature}",
        log1p(col(feature))
    )


# Build the final feature list.
model_features = [
    "log_pop",
    "white_pct",
    "black_pct",
    "hisp_pct",
    "asian_pct",
    "aian_pct",
    "nhpi_pct",
    "other_pct",
    "two_pct",
    "log_property_count",
    "log_median_list_price",
    "log_median_price_per_sqft",
    "log_avg_sqft",
    "log_poi_count",
    "log_food_count",
    "log_grocery_count",
    "log_healthcare_count",
    "log_education_count",
    "log_shopping_count",
    "log_fitness_count",
    "log_recreation_count",
    "log_entertainment_count",
    "log_restaurant_count",
    "log_park_count",
    "log_gym_count",
    "log_hospital_count",
    "log_school_count"
]


# Impute missing feature values using the median.
imputer = Imputer(
    inputCols=model_features,
    outputCols=[
        f"{feature}_imputed"
        for feature in model_features
    ],
    strategy="median"
)

neighborhood = imputer.fit(
    neighborhood
).transform(
    neighborhood
)


# Assemble features into a single vector.
imputed_features = [
    f"{feature}_imputed"
    for feature in model_features
]

assembler = VectorAssembler(
    inputCols=imputed_features,
    outputCol="raw_features"
)

neighborhood = assembler.transform(
    neighborhood
)


# Standardize the feature vector.
scaler = StandardScaler(
    inputCol="raw_features",
    outputCol="scaled_features",
    withMean=True,
    withStd=True
)

scaler_model = scaler.fit(
    neighborhood
)

neighborhood = scaler_model.transform(
    neighborhood
)


# Reduce the feature space using PCA.
pca = PCA(
    k=10,
    inputCol="scaled_features",
    outputCol="features"
)

pca_model = pca.fit(
    neighborhood
)

neighborhood = pca_model.transform(
    neighborhood
)


# Keep neighborhood information and MLlib feature vectors.
neighborhood_vectors = neighborhood.select(
    "city",
    "state",
    "state_abbr",
    "nbhd_id",
    "neighborhood",
    "features"
).cache()


# Build an approximate nearest-neighbor model using Spark MLlib.
lsh = BucketedRandomProjectionLSH(
    inputCol="features",
    outputCol="hashes",
    bucketLength=1.0,
    numHashTables=5,
    seed=42
)

lsh_model = lsh.fit(
    neighborhood_vectors
)


# Save the neighborhood feature vectors.
neighborhood_vectors.write.mode(
    "overwrite"
).parquet(
    "data/processed/neighborhood_similarity_vectors"
)


# Save the MLlib similarity model.
lsh_model.write().overwrite().save(
    "data/processed/neighborhood_similarity_model"
)


# Save the PCA explained variance.
pca_variance = spark.createDataFrame(
    [
        (
            i + 1,
            float(value)
        )
        for i, value in enumerate(
            pca_model.explainedVariance.toArray()
        )
    ],
    [
        "component",
        "explained_variance"
    ]
)

pca_variance.write.mode(
    "overwrite"
).parquet(
    "data/processed/neighborhood_similarity_pca"
)


# Find example similar neighborhoods for Austin.
austin = neighborhood_vectors.filter(
    (col("city") == "Austin") &
    (col("state") == "Texas")
).limit(1)


if austin.count() > 0:

    austin_vector = austin.collect()[0]["features"]

    similar_neighborhoods = (
        lsh_model.approxNearestNeighbors(
            neighborhood_vectors,
            austin_vector,
            11
        )
    )

    similar_neighborhoods = similar_neighborhoods.filter(
        ~(
            (col("city") == "Austin") &
            (col("state") == "Texas") &
            (col("nbhd_id") == austin.collect()[0]["nbhd_id"])
        )
    ).limit(10)

    print(
        "SIMILAR NEIGHBORHOODS TO AUSTIN:",
        flush=True
    )

    similar_neighborhoods.select(
        "city",
        "state",
        "neighborhood",
        "nbhd_id",
        "distCol"
    ).show(
        10,
        False
    )


print(
    "NEIGHBORHOOD SIMILARITY MLlib COMPLETE",
    flush=True
)


spark.stop()