import glob
import os
import re

from pyspark.sql.functions import col, lit
from sedona.spark import SedonaContext


# Create a local Spark session using 4 worker threads.
spark = (
    SedonaContext.builder()
    .appName("CityScope Neighborhood Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# Initialize Sedona
sedona = SedonaContext.create(spark)


state_map = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia"
}


shapefiles = sorted(
    glob.glob("data/raw/neighborhoods/cdnd_data/*_onm_cleaned.shp")
)

neighborhood_dfs = []

for shapefile in shapefiles:

    filename = os.path.basename(shapefile)

    match = re.match(
        r"^(.*?)([A-Z]{2})_onm_cleaned\.shp$",
        filename
    )

    if not match:
        print("SKIPPING:", filename)
        continue

    city = match.group(1)
    state_abbr = match.group(2)
    state = state_map.get(state_abbr)

    if state is None:
        print("UNKNOWN STATE:", filename)
        continue

    df = (
        sedona.read
        .format("shapefile")
        .load(shapefile)
    )

    if "nbhd" in df.columns:
        neighborhood_col = col("nbhd")
    else:
        neighborhood_col = col("FID").cast("string")

    df = (
        df.select(
            lit(city).alias("city"),
            lit(state).alias("state"),
            lit(state_abbr).alias("state_abbr"),
            neighborhood_col.alias("neighborhood"),
            col("geometry")
        )
        .filter(
            col("neighborhood").isNotNull() &
            col("geometry").isNotNull()
        )
    )

    neighborhood_dfs.append(df)


# Combine all city neighborhood datasets.
neighborhoods = neighborhood_dfs[0]

for df in neighborhood_dfs[1:]:
    neighborhoods = neighborhoods.unionByName(df)


# Save cleaned neighborhood boundaries.
neighborhoods.write.mode("overwrite").parquet(
    "data/processed/neighborhoods"
)

spark.stop()