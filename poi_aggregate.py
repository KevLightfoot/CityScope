"""
poi_aggregate.py assigns nationwide POIs to Census Places and
creates city-level POI category summaries.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, expr, broadcast
from sedona.spark import SedonaContext

spark = SparkSession.builder \
    .master("local[4]") \
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
        "geometry",
        "state"
    )

# Convert POI WKB to Sedona geometry
pois = pois.withColumn(
    "poi_geometry",
    expr("ST_GeomFromWKB(geometry)")
)

pois = pois.filter(
    col("poi_geometry").isNotNull()
)

# State FIPS codes
state_fips = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05",
    "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "FL": "12", "GA": "13", "HI": "15", "ID": "16",
    "IL": "17", "IN": "18", "IA": "19", "KS": "20",
    "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32",
    "NH": "33", "NJ": "34", "NM": "35", "NY": "36",
    "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56"
}

# POI categories
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

# Get states with POI data
states = [
    row["state"]
    for row in pois.select("state").distinct().collect()
    if row["state"] in state_fips
]
print("STATES:", len(states))

# Process each state

for state in states:

    print("PROCESSING:", state)

    fips = state_fips[state]

    state_places = places.filter(
        col("place_GEOID").substr(1, 2) == fips
    )

    state_pois = pois.filter(
        col("state") == state
    )

    print("POIs:", state_pois.count())
    print("PLACES:", state_places.count())

# Spatial join: POI falls inside Census Place
    joined = state_pois.join(
        broadcast(state_places),
        expr("ST_Contains(place_geometry, poi_geometry)"),
        "inner"
    ).select(
        "id",
        "cityscope_category",
        "place_GEOID",
        "place_name"
    )

    # Count POIs by city and category
    aggregated = joined.groupBy(
        "place_GEOID",
        "place_name"
    ).pivot(
        "cityscope_category",
        categories
    ).agg(
        count("id")
    ).fillna(0)

    # Rename category columns
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

    # Save state result
    output_path = f"data/processed/poi_city_states/state={state}"

    aggregated.write \
        .mode("overwrite") \
        .parquet(output_path)

    print("COMPLETE:", state)

# Load state results
final = spark.read.parquet(
    "data/processed/poi_city_states"
)

# Save
final.write \
    .mode("overwrite") \
    .parquet("data/processed/poi_city")

print("POI CITY AGGREGATION COMPLETE")

final.orderBy(
    col("poi_total_count").desc()
).show(20, False)

spark.stop()