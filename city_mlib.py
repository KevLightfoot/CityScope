"""
city_mllib.py uses Spark MLlib to cluster CityScope cities based on
demographic, housing, crime, weather, and POI characteristics.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, log1p, coalesce, lit
from pyspark.ml.feature import VectorAssembler, StandardScaler, Imputer
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator


# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope City MLlib")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")


# Read the integrated city-level dataset.
cityscope = spark.read.parquet(
    "data/processed/cityscope_city"
)


# Select the features used for city clustering.
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


# Apply log transformations to heavily skewed count and price features.
log_columns = [
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

for feature in log_columns:
    cityscope = cityscope.withColumn(
        f"log_{feature}",
        log1p(coalesce(col(feature), lit(0)))
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


# Fill missing feature values using the median.
imputer = Imputer(
    inputCols=model_features,
    outputCols=[
        f"{feature}_imputed"
        for feature in model_features
    ],
    strategy="median"
)

cityscope = imputer.fit(cityscope).transform(cityscope)


# Assemble all clustering features into one vector.
imputed_features = [
    f"{feature}_imputed"
    for feature in model_features
]

assembler = VectorAssembler(
    inputCols=imputed_features,
    outputCol="raw_features"
)

cityscope = assembler.transform(cityscope)


# Standardize the feature vectors before clustering.
scaler = StandardScaler(
    inputCol="raw_features",
    outputCol="features",
    withStd=True,
    withMean=True
)

cityscope = scaler.fit(cityscope).transform(cityscope)


# Test multiple KMeans cluster counts.
evaluator = ClusteringEvaluator(
    predictionCol="prediction",
    featuresCol="features",
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

    results.append(
        (k, silhouette)
    )

    print(
        f"K={k} SILHOUETTE={silhouette:.4f}"
    )


# Select the cluster count with the highest silhouette score.
best_k, best_silhouette = max(
    results,
    key=lambda item: item[1]
)

print()
print("BEST K:", best_k)
print("BEST SILHOUETTE:", round(best_silhouette, 4))


# Train the final KMeans model.
final_kmeans = KMeans(
    k=best_k,
    seed=42,
    featuresCol="features",
    predictionCol="cluster"
)

final_model = final_kmeans.fit(cityscope)


# Add final cluster assignments.
clustered = final_model.transform(cityscope)


# Keep the city information and cluster assignment.
clustered = clustered.select(
    "city",
    "state",
    "census_geo_id",
    "population",
    "median_age",
    "median_list_price",
    "median_price_per_sqft",
    "incident_count",
    "avg_temp",
    "poi_total_count",
    "cluster"
)


# Show the number of cities in each cluster.
print()
print("CITIES PER CLUSTER:")

clustered.groupBy(
    "cluster"
).count().orderBy(
    "cluster"
).show()


# Show sample clustered cities.
print("SAMPLE CITY CLUSTERS:")

clustered.orderBy(
    "city",
    "state"
).show(30, False)


# Save city cluster assignments as Parquet.
clustered.write.mode("overwrite").parquet(
    "data/processed/city_mllib"
)


# Save the cluster evaluation results.
spark.createDataFrame(
    results,
    ["k", "silhouette"]
).write.mode("overwrite").parquet(
    "data/processed/city_mllib_evaluation"
)


# Print the output locations.
print("SAVED: data/processed/city_mllib")
print("SAVED: data/processed/city_mllib_evaluation")
print("DONE")


spark.stop()