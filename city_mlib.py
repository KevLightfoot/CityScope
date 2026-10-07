"""
city_mllib.py uses Spark MLlib to cluster CityScope cities based on
demographic, housing, crime, weather, and POI characteristics.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, log1p, coalesce, lit
from pyspark.ml.feature import VectorAssembler, StandardScaler, Imputer
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator


# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope City MLlib")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Read integrated CityScope city-level data.
cityscope = spark.read.parquet(
    "data/processed/cityscope_city"
)


# Select features for clustering.
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


# Replace missing numeric values with zero where appropriate.
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

cityscope = imputer.fit(cityscope).transform(cityscope)


# Assemble features into a single vector.
imputed_features = [
    f"{feature}_imputed"
    for feature in model_features
]

assembler = VectorAssembler(
    inputCols=imputed_features,
    outputCol="raw_features"
)

cityscope = assembler.transform(cityscope)


# Standardize the feature vector.
scaler = StandardScaler(
    inputCol="raw_features",
    outputCol="features",
    withMean=True,
    withStd=True
)

cityscope = scaler.fit(cityscope).transform(cityscope)


# Evaluate K-Means models with different cluster counts.
evaluator = ClusteringEvaluator(
    featuresCol="features",
    predictionCol="prediction",
    metricName="silhouette"
)

results = []

for k in range(2, 9):

    kmeans = KMeans(
        k=k,
        seed=42,
        featuresCol="features",
        predictionCol="prediction"
    )

    model = kmeans.fit(cityscope)

    predictions = model.transform(cityscope)

    silhouette = evaluator.evaluate(predictions)

    results.append((k, silhouette))

    print(
        f"k={k} silhouette={silhouette:.4f}",
        flush=True
    )


# Select the cluster count with the highest silhouette score.
best_k, best_silhouette = max(
    results,
    key=lambda x: x[1]
)

print(
    f"BEST K: {best_k}",
    flush=True
)

print(
    f"BEST SILHOUETTE: {best_silhouette:.4f}",
    flush=True
)


# Train the final K-Means model.
final_kmeans = KMeans(
    k=best_k,
    seed=42,
    featuresCol="features",
    predictionCol="cluster"
)

final_model = final_kmeans.fit(cityscope)

cityscope_clustered = final_model.transform(cityscope)


# Save city cluster assignments.
cityscope_clustered.select(
    "city",
    "state",
    "census_geo_id",
    "cluster"
).write.mode("overwrite").parquet(
    "data/processed/city_mllib"
)


# Save K-Means evaluation results.
evaluation_df = spark.createDataFrame(
    results,
    ["k", "silhouette"]
)

evaluation_df.write.mode("overwrite").parquet(
    "data/processed/city_mllib_evaluation"
)


# Display cluster counts.
cityscope_clustered.groupBy(
    "cluster"
).count().orderBy(
    "cluster"
).show()


spark.stop()