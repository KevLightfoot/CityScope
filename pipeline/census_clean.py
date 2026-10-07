"""
census_clean.py

Cleans the 2024 ACS DP05 Census dataset and adds 2024 ACS DP03
employment data for CityScope.

The script:
1. Reads the raw ACS DP05 demographic dataset.
2. Reads the raw ACS DP03 economic dataset.
3. Selects the demographic and employment fields needed by CityScope.
4. Joins DP03 employment data to DP05 using GEO_ID.
5. Normalizes Census place names and state names.
6. Converts values into usable numeric types.
7. Removes the Census metadata row.
8. Writes the combined result as Parquet.
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
# Read raw Census DP03 employment dataset
# ---------------------------------------------------------

employment_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("data/raw/census/ACSDP5Y2024.DP03-Data.csv")
    .select(

        # Geographic identifier
        col("GEO_ID"),

        # -------------------------------------------------
        # Labor force
        # -------------------------------------------------

        expr(
            "try_cast(DP03_0002E AS BIGINT)"
        ).alias("labor_force"),

        expr(
            "try_cast(DP03_0004E AS BIGINT)"
        ).alias("employed"),

        expr(
            "try_cast(DP03_0005E AS BIGINT)"
        ).alias("unemployed"),

        expr(
            """
            CASE
                WHEN try_cast(DP03_0002E AS DOUBLE) > 0
                THEN try_cast(DP03_0005E AS DOUBLE)
                    / try_cast(DP03_0002E AS DOUBLE) * 100
                ELSE NULL
            END
        """
        ).alias("unemployment_rate"),

        # -------------------------------------------------
        # Occupation percentages
        # -------------------------------------------------

        expr(
            "try_cast(DP03_0027PE AS DOUBLE)"
        ).alias(
            "management_business_science_arts_pct"
        ),

        expr(
            "try_cast(DP03_0028PE AS DOUBLE)"
        ).alias("service_pct"),

        expr(
            "try_cast(DP03_0029PE AS DOUBLE)"
        ).alias("sales_office_pct"),

        expr(
            "try_cast(DP03_0030PE AS DOUBLE)"
        ).alias(
            "natural_resources_construction_maintenance_pct"
        ),

        expr(
            "try_cast(DP03_0031PE AS DOUBLE)"
        ).alias(
            "production_transportation_pct"
        ),

        # -------------------------------------------------
        # Industry percentages
        # -------------------------------------------------

        expr(
            "try_cast(DP03_0034PE AS DOUBLE)"
        ).alias("construction_pct"),

        expr(
            "try_cast(DP03_0035PE AS DOUBLE)"
        ).alias("manufacturing_pct"),

        expr(
            "try_cast(DP03_0037PE AS DOUBLE)"
        ).alias("retail_pct"),

        expr(
            "try_cast(DP03_0038PE AS DOUBLE)"
        ).alias("transportation_utilities_pct"),

        expr(
            "try_cast(DP03_0039PE AS DOUBLE)"
        ).alias("information_pct"),

        expr(
            "try_cast(DP03_0040PE AS DOUBLE)"
        ).alias("finance_real_estate_pct"),

        expr(
            "try_cast(DP03_0041PE AS DOUBLE)"
        ).alias("professional_services_pct"),

        expr(
            "try_cast(DP03_0042PE AS DOUBLE)"
        ).alias("education_healthcare_pct"),

        expr(
            "try_cast(DP03_0043PE AS DOUBLE)"
        ).alias("arts_accommodation_food_pct"),

        expr(
            "try_cast(DP03_0045PE AS DOUBLE)"
        ).alias("public_admin_pct")
    )

    # Remove Census metadata row.
    .filter(col("GEO_ID") != "Geography")
)


# ---------------------------------------------------------
# Clean and normalize Census DP05 data
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

    # Remove Census metadata row.
    .filter(col("GEO_ID") != "Geography")

    # -----------------------------------------------------
    # Join employment data
    # -----------------------------------------------------

    .join(
        employment_df,
        on="GEO_ID",
        how="left"
    )

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


# ---------------------------------------------------------
# Employment validation
# ---------------------------------------------------------

print("\nEmployment validation:")

clean_df.select(
    "city_name",
    "state",
    "labor_force",
    "employed",
    "unemployed",
    "unemployment_rate",
    "management_business_science_arts_pct",
    "service_pct",
    "sales_office_pct",
    "construction_pct",
    "manufacturing_pct",
    "education_healthcare_pct"
).filter(
    (col("city_name") == "Austin") &
    (col("state") == "Texas")
).show(
    truncate=False
)


# ---------------------------------------------------------
# Geography validation
# ---------------------------------------------------------

print("\nGeography validation:")

clean_df.select(
    "NAME",
    "city_name",
    "place_type",
    "state",
    "city_key",
    "state_key"
).show(
    10,
    truncate=False
)


# ---------------------------------------------------------
# Stop Spark
# ---------------------------------------------------------

spark.stop()