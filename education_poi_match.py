"""
education_poi_match.py matches Overture school POIs with
school-level education data for CityScope.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    lower,
    upper,
    trim,
    regexp_replace,
    when,
    create_map,
    count
)


# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder
    .appName("CityScope Education POI Matching")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")


# Define state name to abbreviation mappings.
state_map = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
}

state_expr = create_map(
    *[
        x
        for pair in state_map.items()
        for x in (lit(pair[0]), lit(pair[1]))
    ]
)


# Normalize state values into two-letter abbreviations.
def normalize_state(column):
    value = upper(trim(column))

    return when(
        value.isNull(),
        lit(None).cast("string")
    ).when(
        value.rlike("^[A-Z]{2}$"),
        value
    ).otherwise(
        state_expr.getItem(value)
    )


# Normalize school names for matching.
def normalize_school_name(column):
    name = lower(trim(column))

    # Normalize ampersands and remove punctuation.
    name = regexp_replace(name, "&", " and ")
    name = regexp_replace(name, r"[^a-z0-9]+", " ")

    # Remove a leading "the".
    name = regexp_replace(name, r"^the ", "")

    # Collapse repeated whitespace.
    name = regexp_replace(name, r"\s+", " ")

    return trim(name)


# Read cleaned education data.
education = spark.read.parquet(
    "data/processed/education_clean"
)


# Read school POIs with original Overture city values.
school_pois = spark.read.parquet(
    "data/processed/school_poi_city"
)


# Normalize education state and school name values.
education = (
    education
    .withColumn(
        "match_state",
        normalize_state(col("state"))
    )
    .withColumn(
        "match_name",
        normalize_school_name(col("school"))
    )
)


# Normalize school POI state and name values.
school_pois = (
    school_pois
    .withColumn(
        "match_state",
        normalize_state(col("state"))
    )
    .withColumn(
        "match_name",
        normalize_school_name(col("name"))
    )
)


# Count education records for each state and school name.
education_name_counts = (
    education
    .filter(
        col("match_state").isNotNull() &
        col("match_name").isNotNull() &
        (col("match_name") != "")
    )
    .groupBy(
        "match_state",
        "match_name"
    )
    .agg(
        count("*").alias("education_records")
    )
)


# Keep only education records with unique state and school names.
unique_education_keys = (
    education_name_counts
    .filter(
        col("education_records") == 1
    )
    .select(
        "match_state",
        "match_name"
    )
)


# Keep the education fields needed for POI enrichment.
education_unique = (
    education
    .join(
        unique_education_keys,
        ["match_state", "match_name"],
        "inner"
    )
    .select(
        "match_state",
        "match_name",
        "ncesschid",
        "school",
        "math_pct",
        "ela_pct",
        "graduation_pct",
        "school_quality_score"
    )
)


# Match school POIs to uniquely identified education records.
matched = (
    school_pois
    .join(
        education_unique,
        ["match_state", "match_name"],
        "left"
    )
)


# Mark school POIs that received an education record.
matched = matched.withColumn(
    "education_match",
    when(
        col("ncesschid").isNotNull(),
        lit(True)
    ).otherwise(
        lit(False)
    )
)


# Remove temporary matching fields.
matched = matched.drop(
    "match_state",
    "match_name"
)


# Calculate school POI match statistics.
total = matched.count()

matched_count = (
    matched
    .filter(col("education_match"))
    .count()
)

unmatched_count = total - matched_count


# Print school POI match statistics.
print("SCHOOL POIs:", total)
print("MATCHED:", matched_count)
print("UNMATCHED:", unmatched_count)

if total > 0:
    print(
        "MATCH RATE:",
        round((matched_count / total) * 100, 2),
        "%"
    )


# Show sample matched school POIs.
print()
print("SAMPLE MATCHES:")

matched.filter(
    col("education_match")
).select(
    "id",
    "name",
    "city",
    "state",
    "school",
    "math_pct",
    "ela_pct",
    "graduation_pct",
    "school_quality_score"
).show(20, False)


# Save enriched school POIs as Parquet.
matched.write.mode("overwrite").parquet(
    "data/processed/school_poi_education"
)


# Print the output location.
print()
print("SAVED: data/processed/school_poi_education")
print("DONE")


spark.stop()