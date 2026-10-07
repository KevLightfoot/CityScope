"""
city_mllib.py uses Spark MLlib to create nationwide city feature vectors
and an approximate nearest-neighbor similarity model.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, log1p
from pyspark.ml.feature import VectorAssembler, StandardScaler, Imputer, PCA
from pyspark.ml.feature import BucketedRandomProjectionLSH


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope City Similarity MLlib")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read integrated CityScope city-level data.
cityscope = spark.read.parquet(
    "data/processed/cityscope_city"
)


# Features used to represent city characteristics.
feature_columns = [
    "population",
    "median_age",
    "under_18_pct",
    "age_65_plus_pct",
    "white_pct",
    "black_pct",
    "asian_pct",
    "hispanic_latino_pct",
    "median_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "incident_count",
    "avg_temp",
    "poi_total_count",
    "poi_food_count",
    "poi_grocery_count",
    "poi_healthcare_count",
    "poi_education_count",
    "poi_shopping_count",
    "poi_recreation_count",
    "poi_entertainment_count"
]


# Replace missing count values with zero.
cityscope = cityscope.fillna(
    0,
    subset=[
        "incident_count",
        "poi_total_count",
        "poi_food_count",
        "poi_grocery_count",
        "poi_healthcare_count",
        "poi_education_count",
        "poi_shopping_count",
        "poi_recreation_count",
        "poi_entertainment_count"
    ]
)


# Log-transform highly skewed count and price features.
log_features = [
    "population",
    "median_list_price",
    "median_price_per_sqft",
    "avg_sqft",
    "incident_count",
    "poi_total_count",
    "poi_food_count",
    "poi_grocery_count",
    "poi_healthcare_count",
    "poi_education_count",
    "poi_shopping_count",
    "poi_recreation_count",
    "poi_entertainment_count"
]

for feature in log_features:
    cityscope = cityscope.withColumn(
        f"log_{feature}",
        log1p(col(feature))
    )


# Build the final feature list.
model_features = [
    "log_population",
    "median_age",
    "under_18_pct",
    "age_65_plus_pct",
    "white_pct",
    "black_pct",
    "asian_pct",
    "hispanic_latino_pct",
    "log_median_list_price",
    "log_median_price_per_sqft",
    "log_avg_sqft",
    "log_incident_count",
    "avg_temp",
    "log_poi_total_count",
    "log_poi_food_count",
    "log_poi_grocery_count",
    "log_poi_healthcare_count",
    "log_poi_education_count",
    "log_poi_shopping_count",
    "log_poi_recreation_count",
    "log_poi_entertainment_count"
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

cityscope = imputer.fit(
    cityscope
).transform(
    cityscope
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

cityscope = assembler.transform(
    cityscope
)


# Standardize the feature vector.
scaler = StandardScaler(
    inputCol="raw_features",
    outputCol="scaled_features",
    withMean=True,
    withStd=True
)

scaler_model = scaler.fit(
    cityscope
)

cityscope = scaler_model.transform(
    cityscope
)


# Reduce the feature space using PCA.
pca = PCA(
    k=10,
    inputCol="scaled_features",
    outputCol="features"
)

pca_model = pca.fit(
    cityscope
)

cityscope = pca_model.transform(
    cityscope
)


# Keep the city information and MLlib feature vector.
city_vectors = cityscope.select(
    "city",
    "state",
    "census_geo_id",
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
    city_vectors
)


# Save the city feature vectors.
city_vectors.write.mode(
    "overwrite"
).parquet(
    "data/processed/city_similarity_vectors"
)


# Save the MLlib similarity model.
lsh_model.write().overwrite().save(
    "data/processed/city_similarity_model"
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
    "data/processed/city_similarity_pca"
)


print(
    "CITY SIMILARITY MLlib COMPLETE",
    flush=True
)


spark.stop()