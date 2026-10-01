"""
census_clean.py

Cleans the 2024 ACS DP05 Census dataset for CityScope.

The script:
1. Reads the raw ACS DP05 dataset using PySpark.
2. Selects the demographic fields needed by CityScope.
3. Normalizes Census place names and state names.
4. Converts demographic values into usable numeric types.
5. Removes the Census metadata row.
6. Writes the cleaned result as Parquet.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    expr,
    regexp_extract,
    regexp_replace,
    lower,
    trim
)


# ---------------------------------------------------------
# Create Spark session
# ---------------------------------------------------------

spark = (
    SparkSession.builder
    .appName("CityScope Census Cleaning")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ---------------------------------------------------------
# Read raw Census DP05 dataset
# ---------------------------------------------------------

census_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("data/raw/census/ACSDP5Y2024.DP05-Data.csv")
)


# ---------------------------------------------------------
# Clean and normalize Census data
# ---------------------------------------------------------

clean_df = (
    census_df
    .select(

        # Geographic information
        col("GEO_ID"),
        col("NAME"),

        # -------------------------------------------------
        # Population / age
        # -------------------------------------------------

        expr(
            "try_cast(DP05_0001E AS BIGINT)"
        ).alias("population"),

        expr(
            "try_cast(DP05_0018E AS DOUBLE)"
        ).alias("median_age"),

        expr(
            "try_cast(DP05_0005PE AS DOUBLE)"
        ).alias("under_5_pct"),

        expr(
            "try_cast(DP05_0006PE AS DOUBLE)"
        ).alias("age_5_9_pct"),

        expr(
            "try_cast(DP05_0007PE AS DOUBLE)"
        ).alias("age_10_14_pct"),

        expr(
            "try_cast(DP05_0008PE AS DOUBLE)"
        ).alias("age_15_19_pct"),

        expr(
            "try_cast(DP05_0009PE AS DOUBLE)"
        ).alias("age_20_24_pct"),

        expr(
            "try_cast(DP05_0010PE AS DOUBLE)"
        ).alias("age_25_34_pct"),

        expr(
            "try_cast(DP05_0011PE AS DOUBLE)"
        ).alias("age_35_44_pct"),

        expr(
            "try_cast(DP05_0012PE AS DOUBLE)"
        ).alias("age_45_54_pct"),

        expr(
            "try_cast(DP05_0013PE AS DOUBLE)"
        ).alias("age_55_59_pct"),

        expr(
            "try_cast(DP05_0014PE AS DOUBLE)"
        ).alias("age_60_64_pct"),

        expr(
            "try_cast(DP05_0015PE AS DOUBLE)"
        ).alias("age_65_74_pct"),

        expr(
            "try_cast(DP05_0016PE AS DOUBLE)"
        ).alias("age_75_84_pct"),

        expr(
            "try_cast(DP05_0017PE AS DOUBLE)"
        ).alias("age_85_plus_pct"),

        expr(
            "try_cast(DP05_0019PE AS DOUBLE)"
        ).alias("under_18_pct"),

        expr(
            "try_cast(DP05_0021PE AS DOUBLE)"
        ).alias("age_18_plus_pct"),

        expr(
            "try_cast(DP05_0022PE AS DOUBLE)"
        ).alias("age_21_plus_pct"),

        expr(
            "try_cast(DP05_0023PE AS DOUBLE)"
        ).alias("age_62_plus_pct"),

        expr(
            "try_cast(DP05_0024PE AS DOUBLE)"
        ).alias("age_65_plus_pct"),

        # -------------------------------------------------
        # Sex
        # -------------------------------------------------

        expr(
            "try_cast(DP05_0002PE AS DOUBLE)"
        ).alias("male_pct"),

        expr(
            "try_cast(DP05_0003PE AS DOUBLE)"
        ).alias("female_pct"),

        expr(
            "try_cast(DP05_0004E AS DOUBLE)"
        ).alias("sex_ratio"),

        # -------------------------------------------------
        # Race
        # -------------------------------------------------

        expr(
            "try_cast(DP05_0037PE AS DOUBLE)"
        ).alias("white_pct"),

        expr(
            "try_cast(DP05_0045PE AS DOUBLE)"
        ).alias("black_pct"),

        expr(
            "try_cast(DP05_0053PE AS DOUBLE)"
        ).alias("american_indian_alaska_native_pct"),

        expr(
            "try_cast(DP05_0061PE AS DOUBLE)"
        ).alias("asian_pct"),

        expr(
            "try_cast(DP05_0069PE AS DOUBLE)"
        ).alias("native_hawaiian_pacific_islander_pct"),

        expr(
            "try_cast(DP05_0074PE AS DOUBLE)"
        ).alias("other_race_pct"),

        expr(
            "try_cast(DP05_0075PE AS DOUBLE)"
        ).alias("two_or_more_races_pct"),

        # -------------------------------------------------
        # Hispanic / Latino
        # -------------------------------------------------

        expr(
            "try_cast(DP05_0090PE AS DOUBLE)"
        ).alias("hispanic_latino_pct")
    )

    # Remove the Census metadata row.
    .filter(col("GEO_ID") != "Geography")

    # -----------------------------------------------------
    # Normalize geographic names
    #
    # Example:
    # "Austin city, Texas"
    #
    # becomes:
    # city_name = "Austin"
    # state     = "Texas"
    # city_key  = "austin"
    # -----------------------------------------------------

    .withColumn(
        "city_name",
        regexp_extract(
            col("NAME"),
            r"^(.*),\s*[^,]+$",
            1
        )
    )

    .withColumn(
        "place_type",
        regexp_extract(
            col("NAME"),
            r"\s+(city|town|village|CDP),\s*[^,]+$",
            1
        )
    )

    .withColumn(
        "city_name",
        regexp_replace(
            col("city_name"),
            r"\s+(city|town|village|CDP)$",
            ""
        )
    )

    .withColumn(
        "state",
        regexp_extract(
            col("NAME"),
            r",\s*([^,]+)$",
            1
        )
    )

    .withColumn(
        "city_key",
        lower(trim(col("city_name")))
    )

    .withColumn(
        "state_key",
        lower(trim(col("state")))
    )
)


# ---------------------------------------------------------
# Write cleaned Census data
# ---------------------------------------------------------

clean_df.write \
    .mode("overwrite") \
    .parquet("data/processed/census_clean")


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("Census cleaning complete.")
print(f"Records written: {clean_df.count()}")

print("\nCleaned Census schema:")
clean_df.printSchema()

print("\nGeography validation:")
clean_df.select(
    "NAME",
    "city_name",
    "state",
    "city_key",
    "state_key"
).show(10, truncate=False)


# ---------------------------------------------------------
# Stop Spark
# ---------------------------------------------------------

spark.stop()