import glob
import os
import re
import shutil
import subprocess

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

# Initialize Sedona.
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
    glob.glob(
        "data/raw/neighborhoods/cdnd_data/*_onm_cleaned.shp"
    )
)


# Temporary directory containing all neighborhoods converted to WGS84.
normalized_dir = "/tmp/cityscope_neighborhoods_wgs84"

if os.path.exists(normalized_dir):
    shutil.rmtree(normalized_dir)

os.makedirs(normalized_dir)

neighborhood_dfs = []
failed = []


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

    print("NORMALIZING:", city, state_abbr)

    city_dir = os.path.join(
        normalized_dir,
        f"{city}{state_abbr}"
    )

    os.makedirs(city_dir)

    layer_name = os.path.splitext(filename)[0]

    # Convert to WGS84 and create a 0-based feature ID.
    # CDNB nbhd_id is 1-based, so:
    # feature 0 -> nbhd_id 1
    # feature 1 -> nbhd_id 2
    # etc.
    sql = (
        f'SELECT ROWID AS nbhd_fid, * '
        f'FROM "{layer_name}"'
    )

    result = subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "ESRI Shapefile",
            "-t_srs",
            "EPSG:4326",
            "-dialect",
            "SQLite",
            "-sql",
            sql,
            city_dir,
            shapefile
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("FAILED:", filename)
        print(result.stderr)
        failed.append(filename)
        continue

    normalized_shapefile = os.path.join(
        city_dir,
        filename
    )

    df = (
        sedona.read
        .format("shapefile")
        .load(normalized_shapefile)
    )

    # GDAL created nbhd_fid before Sedona loaded the file.
    df = df.withColumn(
        "nbhd_id",
        col("nbhd_fid").cast("long") + lit(1)
    )

    if "nbhd" in df.columns:
        neighborhood_col = col("nbhd").cast("string")
    else:
        neighborhood_col = lit(None).cast("string")

    df = (
        df.select(
            lit(city).alias("city"),
            lit(state).alias("state"),
            lit(state_abbr).alias("state_abbr"),
            col("nbhd_id"),
            neighborhood_col.alias("neighborhood"),
            col("geometry")
        )
        .filter(
            col("geometry").isNotNull()
        )
    )

    neighborhood_dfs.append(df)


if failed:
    print("\nFAILED FILES:")
    for filename in failed:
        print(filename)

    raise RuntimeError(
        f"{len(failed)} neighborhood files failed CRS normalization."
    )


# Combine all city neighborhood datasets.
neighborhoods = neighborhood_dfs[0]

for df in neighborhood_dfs[1:]:
    neighborhoods = neighborhoods.unionByName(df)


# Save cleaned neighborhood boundaries.
neighborhoods.write.mode("overwrite").parquet(
    "data/processed/neighborhoods"
)


print("\nROWS:", neighborhoods.count())
print("CITIES:", neighborhoods.select("city").distinct().count())
print("STATES:", neighborhoods.select("state").distinct().count())

spark.stop()