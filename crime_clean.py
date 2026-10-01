"""
crime_clean.py takes administrative crime and offense records, cleans them, 
and cross references them against a batch header file for city assignment
"""

from pyspark.sql import SparkSession

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("CityScope Crime Cleaning")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# Read administrative data and keep important fields
administrative_df = (
    spark.read
    .parquet("data/raw/crime/nibrs_administrative_segment_2024.parquet")
    .select(
        "unique_incident_id",
        "ori",
        "incident_date",
        "state_abb"
    )
)

# Read offense data and keep important fields
offense_df = (
    spark.read
    .parquet("data/raw/crime/nibrs_offense_segment_2024.parquet")
    .select(
        "unique_incident_id",
        "ucr_offense_code",
        "location_type",
        "offense_attempted_or_completed"
    )
)

# Read batch header to assign offenses to reporting offices 
batch_header_df = (
    spark.read
    .parquet("data/raw/crime/nibrs_batch_header_1991_2024.parquet")
    .select(
        "ori",
        "city_name",
        "state_abbreviation",
        "population",
        "year"
    )
    .filter("year = 2024")
)

# Inner join on administrative and offense data 
crime_joined = (
    administrative_df.join(
        offense_df,
        "unique_incident_id",
        "inner"
    )
)

# Spatially enrich crime_joined using batch_header data
crime_enriched = (
    crime_joined.join(
        batch_header_df,
        "ori",
        "inner"
    )
)

# Final parquet write
crime_enriched.write.mode("overwrite").parquet("data/processed/crime")

spark.stop()

