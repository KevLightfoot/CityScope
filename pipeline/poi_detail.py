"""
poi_detail.py assigns nationwide POIs to Census Places and
preserves individual POI records for CityScope map exploration.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, broadcast
from sedona.spark import SedonaContext


spark = (
    SparkSession.builder
    .master("local[4]")
    .appName("CityScope_POI_Detail")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.7.0-28.5"
    )
    .getOrCreate()
)

spark = SedonaContext.create(spark)
spark.sparkContext.setLogLevel("ERROR")


# ---------------------------------------------------------
# Census Places
# ---------------------------------------------------------

places = (
    spark.read.parquet("data/processed/places")
    .select(
        col("GEOID").alias("place_GEOID"),
        col("NAME").alias("place_name"),
        col("geometry").alias("place_geometry")
    )
)


# ---------------------------------------------------------
# Nationwide POIs
# ---------------------------------------------------------

pois = (
    spark.read.parquet("data/processed/poi")
    .select(
        "id",
        "name",
        "cityscope_category",
        "category",
        "basic_category",
        "confidence",
        "geometry",
        "state"
    )
)


# Convert WKB → Sedona geometry
pois = (
    pois
    .withColumn(
        "poi_geometry",
        expr("ST_GeomFromWKB(geometry)")
    )
    .filter(
        col("poi_geometry").isNotNull()
    )
)


# ---------------------------------------------------------
# State FIPS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# States with POI data
# ---------------------------------------------------------

states = [
    row["state"]
    for row in pois.select("state").distinct().collect()
    if row["state"] in state_fips
]

print("STATES:", len(states))


# ---------------------------------------------------------
# Spatial assignment
# ---------------------------------------------------------

for state in states:

    print("\nPROCESSING:", state)

    fips = state_fips[state]

    state_places = places.filter(
        col("place_GEOID").substr(1, 2) == fips
    )

    state_pois = pois.filter(
        col("state") == state
    )

    print("POIs:", state_pois.count())
    print("PLACES:", state_places.count())

    # Assign each POI to the Census Place containing it
    joined = (
        state_pois
        .join(
            broadcast(state_places),
            expr(
                "ST_Contains(place_geometry, poi_geometry)"
            ),
            "inner"
        )
        .select(
            "id",
            "name",
            "cityscope_category",
            "category",
            "basic_category",
            "confidence",
            "state",
            "place_GEOID",
            "place_name",
            "poi_geometry"
        )
    )

    # -----------------------------------------------------
    # Extract longitude / latitude
    # -----------------------------------------------------

    joined = (
        joined
        .withColumn(
            "longitude",
            expr("ST_X(ST_Centroid(poi_geometry))")
        )
        .withColumn(
            "latitude",
            expr("ST_Y(ST_Centroid(poi_geometry))")
        )
        .drop("poi_geometry")
    )

    # -----------------------------------------------------
    # Save state partition
    # -----------------------------------------------------

    output_path = (
        f"data/processed/poi_detail_states/state={state}"
    )

    (
        joined
        .write
        .mode("overwrite")
        .parquet(output_path)
    )

    print("COMPLETE:", state)


# ---------------------------------------------------------
# Combine state outputs
# ---------------------------------------------------------

print("\nCOMBINING STATE OUTPUTS...")

final = spark.read.parquet(
    "data/processed/poi_detail_states"
)


# ---------------------------------------------------------
# Save final detail dataset
# ---------------------------------------------------------

(
    final
    .write
    .mode("overwrite")
    .partitionBy(
        "state",
        "cityscope_category"
    )
    .parquet(
        "data/processed/poi_detail"
    )
)


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

print("\nPOI DETAIL COMPLETE")

print("ROWS:", final.count())

final.select(
    "id",
    "name",
    "cityscope_category",
    "place_GEOID",
    "place_name",
    "state",
    "longitude",
    "latitude"
).show(20, False)


spark.stop()