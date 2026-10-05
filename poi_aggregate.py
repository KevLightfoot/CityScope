from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, expr
from sedona.spark import SedonaContext

spark = SparkSession.builder \
    .master("local[2]") \
    .appName("CityScope_POI_Aggregation") \
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.7.0-28.5"
    ) \
    .getOrCreate()

spark = SedonaContext.create(spark)

# Load Census Places
places = spark.read.parquet("data/processed/places") \
    .select(
        col("GEOID").alias("place_GEOID"),
        col("NAME").alias("place_name"),
        col("geometry").alias("place_geometry")
    )


# Load nationwide POIs
pois = spark.read.parquet("data/processed/poi") \
    .select(
        "id",
        "cityscope_category",
        "geometry"
    )

# Convert POI WKB to Sedona geometry
pois = pois.withColumn(
    "poi_geometry",
    expr("ST_GeomFromWKB(geometry)")
)

pois = pois.filter(col("poi_geometry").isNotNull())

print("POI COUNT:", pois.count())
print("PLACE COUNT:", places.count())

# Spatial join: POI falls inside Census Place
joined = pois.join(
    places,
    expr("ST_Contains(place_geometry, poi_geometry)"),
    "inner"
)

print("JOINED POI COUNT:", joined.count())

# Count POIs by city and category
aggregated = joined.groupBy(
    "place_GEOID",
    "place_name"
).pivot(
    "cityscope_category"
).agg(
    count("id")
).fillna(0)

# Rename category columns
categories = [
    "food",
    "grocery",
    "healthcare",
    "education",
    "shopping",
    "financial",
    "fitness",
    "recreation",
    "entertainment",
    "transportation",
    "lodging",
    "religious",
    "other"
]

for category in categories:
    if category in aggregated.columns:
        aggregated = aggregated.withColumnRenamed(
            category,
            f"poi_{category}_count"
        )

# Total POIs
poi_columns = [
    f"poi_{category}_count"
    for category in categories
    if f"poi_{category}_count" in aggregated.columns
]

total_expr = col(poi_columns[0])

for c in poi_columns[1:]:
    total_expr = total_expr + col(c)

aggregated = aggregated.withColumn(
    "poi_total_count",
    total_expr
)

# Save
aggregated.write \
    .mode("overwrite") \
    .parquet("data/processed/poi_city")

print("POI CITY AGGREGATION COMPLETE")

aggregated.orderBy(
    col("poi_total_count").desc()
).show(20, False)

spark.stop()