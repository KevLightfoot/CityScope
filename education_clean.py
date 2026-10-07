"""
education_clean.py cleans school-level education data and creates
a composite school quality score
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, regexp_replace, when, lit,
    avg, round
)


spark = SparkSession.builder \
    .appName("CityScope Education Clean") \
    .getOrCreate()


# Read existing education datasets
math_df = spark.read.option("header", True).option("inferSchema", True) \
    .csv("data/raw/education/edfacts_2022_school_math.csv")

ela_df = spark.read.option("header", True).option("inferSchema", True) \
    .csv("data/raw/education/edfacts_2022_school_ela.csv")

grad_df = spark.read.option("header", True).option("inferSchema", True) \
    .csv("data/raw/education/graduation.csv")


# Math
math_df = math_df.filter(
    (col("DataLevel") == "School") &
    (col("Population") == "All Students") &
    (col("AgeGrade") == "All Grades") &
    (col("Subgroup") == "All Students in School")
).select(
    col("NCESSCHID").cast("string").alias("ncesschid"),
    col("State").alias("state"),
    col("School").alias("school"),
    col("ProficientOrAbove_percent").alias("math_raw")
)


# ELA
ela_df = ela_df.filter(
    (col("DataLevel") == "School") &
    (col("Population") == "All Students") &
    (col("AgeGrade") == "All Grades") &
    (col("Subgroup") == "All Students in School")
).select(
    col("NCESSCHID").cast("string").alias("ncesschid"),
    col("ProficientOrAbove_percent").alias("ela_raw")
)


# Graduation
grad_df = grad_df.filter(
    (col("Population") == "All Students") &
    (col("Subgroup") == "All Students in School") &
    col("Data Description").contains("Four-Year Adjusted-Cohort Graduation Rate")
).select(
    col("NCES SCH ID").cast("string").alias("ncesschid"),
    col("Value").alias("graduation_raw")
)


# Convert achievement ranges to midpoint percentages
def convert_range(column):
    cleaned = regexp_replace(column, "%", "")

    return (
        when(cleaned.startswith("<="),
             regexp_replace(cleaned, "<=", "").cast("double") / 2)
        .when(cleaned.startswith(">="),
              regexp_replace(cleaned, ">=", "").cast("double"))
        .when(cleaned.contains("-"),
              (
                  regexp_replace(cleaned, "-.*", "").cast("double") +
                  regexp_replace(cleaned, ".*-", "").cast("double")
              ) / 2)
        .otherwise(cleaned.cast("double"))
    )


math_df = math_df.withColumn("math_pct", convert_range(col("math_raw")))
ela_df = ela_df.withColumn("ela_pct", convert_range(col("ela_raw")))

grad_df = grad_df.withColumn(
    "graduation_pct",
    regexp_replace(col("graduation_raw"), "%", "").cast("double")
)


# Remove duplicate school records
math_df = math_df.dropDuplicates(["ncesschid"])
ela_df = ela_df.dropDuplicates(["ncesschid"])
grad_df = grad_df.dropDuplicates(["ncesschid"])


# Join
education = math_df.drop("math_raw") \
    .join(ela_df.drop("ela_raw"), ["ncesschid"], "outer") \
    .join(grad_df.drop("graduation_raw"), ["ncesschid"], "outer")


# Create composite school quality score
education = education.withColumn(
    "school_quality_score",
    round(
        (
            when(col("math_pct").isNotNull(), col("math_pct")).otherwise(lit(0)) +
            when(col("ela_pct").isNotNull(), col("ela_pct")).otherwise(lit(0)) +
            when(col("graduation_pct").isNotNull(), col("graduation_pct")).otherwise(lit(0))
        ) /
        (
            when(col("math_pct").isNotNull(), lit(1)).otherwise(lit(0)) +
            when(col("ela_pct").isNotNull(), lit(1)).otherwise(lit(0)) +
            when(col("graduation_pct").isNotNull(), lit(1)).otherwise(lit(0))
        ),
        2
    )
)


# Verification
print("EDUCATION ROWS:", education.count())
print("COLUMNS:", education.columns)

print("MATH NON-NULL:", education.filter(col("math_pct").isNotNull()).count())
print("ELA NON-NULL:", education.filter(col("ela_pct").isNotNull()).count())
print("GRADUATION NON-NULL:", education.filter(col("graduation_pct").isNotNull()).count())
print("QUALITY SCORE NON-NULL:", education.filter(col("school_quality_score").isNotNull()).count())

education.select(
    "ncesschid",
    "state",
    "school",
    "math_pct",
    "ela_pct",
    "graduation_pct",
    "school_quality_score"
).show(20, False)


# Write cleaned education data
education.write.mode("overwrite") \
    .parquet("data/processed/education_clean")


spark.stop()