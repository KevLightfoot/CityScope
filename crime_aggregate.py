"""
crime_aggregate.py aggregates cleaned NIBRS offense records 
into city-level crime metrics
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count_distinct, lower, trim, when, create_map, lit

# Create Spark session
spark = (
    SparkSession.builder
    .appName("CityScope Crime Aggregation")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Read processed crime data
crime_df = (
    spark.read
    .parquet("data/processed/crime")
)

# Normalize city and state values for cross-dataset joins.
crime_df = (
    crime_df
    .withColumn(
        "city_key",
        lower(trim(col("city_name")))
    )
    .withColumn(
        "state_key",
        create_map(
            lit("al"), lit("alabama"),
            lit("ak"), lit("alaska"),
            lit("az"), lit("arizona"),
            lit("ar"), lit("arkansas"),
            lit("ca"), lit("california"),
            lit("co"), lit("colorado"),
            lit("ct"), lit("connecticut"),
            lit("de"), lit("delaware"),
            lit("dc"), lit("district of columbia"),
            lit("fl"), lit("florida"),
            lit("ga"), lit("georgia"),
            lit("hi"), lit("hawaii"),
            lit("id"), lit("idaho"),
            lit("il"), lit("illinois"),
            lit("in"), lit("indiana"),
            lit("ia"), lit("iowa"),
            lit("ks"), lit("kansas"),
            lit("ky"), lit("kentucky"),
            lit("la"), lit("louisiana"),
            lit("me"), lit("maine"),
            lit("md"), lit("maryland"),
            lit("ma"), lit("massachusetts"),
            lit("mi"), lit("michigan"),
            lit("mn"), lit("minnesota"),
            lit("ms"), lit("mississippi"),
            lit("mo"), lit("missouri"),
            lit("mt"), lit("montana"),
            lit("nb"), lit("nebraska"),
            lit("nv"), lit("nevada"),
            lit("nh"), lit("new hampshire"),
            lit("nj"), lit("new jersey"),
            lit("nm"), lit("new mexico"),
            lit("ny"), lit("new york"),
            lit("nc"), lit("north carolina"),
            lit("nd"), lit("north dakota"),
            lit("oh"), lit("ohio"),
            lit("ok"), lit("oklahoma"),
            lit("or"), lit("oregon"),
            lit("pa"), lit("pennsylvania"),
            lit("ri"), lit("rhode island"),
            lit("sc"), lit("south carolina"),
            lit("sd"), lit("south dakota"),
            lit("tn"), lit("tennessee"),
            lit("tx"), lit("texas"),
            lit("ut"), lit("utah"),
            lit("vt"), lit("vermont"),
            lit("va"), lit("virginia"),
            lit("wa"), lit("washington"),
            lit("wv"), lit("west virginia"),
            lit("wi"), lit("wisconsin"),
            lit("wy"), lit("wyoming")
        )[lower(trim(col("state_abbreviation")))]
    )
)

# Group by city and state
# and aggregate by unique incidents
crime_city = (
    crime_df.groupBy(
        "city_name", "state_abbreviation", "city_key", "state_key"
    )
    .agg(
        count_distinct("unique_incident_id")
        .alias("incident_count")
    )
)

# Write finalized parquet
crime_city.write.mode("overwrite").parquet("data/processed/crime_city")

spark.stop()