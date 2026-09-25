"""
crime_clean.py takes administrative crime and offense records, cleans them, 
and cross references them against a batch header file for city assignment
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("CityScope Crime Cleaning")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

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

crime_joined = (
    administrative_df.join(
        offense_df,
        "unique_incident_id",
        "inner"
    )
)

crime_enriched = (
    crime_joined.join(
        batch_header_df,
        "ori",
        "inner"
    )
)

crime_enriched.write.mode("overwrite").parquet("data/processed/crime")

spark.stop()

