"""
clean_nbhd_names looks for non normal named neighborhoods and fixes them
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, when


spark = (
    SparkSession.builder
    .appName("CityScope Neighborhood Name Cleanup")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


paths = {
    "neighborhoods": (
        "data/processed/neighborhoods",
        "neighborhood"
    ),
    "neighborhood_demographics": (
        "data/processed/neighborhood_demographics",
        "nbhd_name"
    ),
    "neighborhood_housing": (
        "data/processed/neighborhood_housing",
        "neighborhood"
    ),
    "neighborhood_poi": (
        "data/processed/neighborhood_poi",
        "neighborhood"
    ),
    "neighborhood_cityscope": (
        "data/processed/neighborhood_cityscope",
        "nbhd_name"
    )
}


for name, (path, name_column) in paths.items():

    df = spark.read.parquet(path)

    cleaned_name = when(
        col(name_column).isNull(),
        col(name_column)
    ).when(
        lower(col(name_column)).startswith("http://"),
        None
    ).when(
        lower(col(name_column)).startswith("https://"),
        None
    ).otherwise(
        col(name_column)
    )

    df = df.withColumn(
        name_column,
        cleaned_name
    )

    df.write.mode("overwrite").parquet(path)

    print(
        name,
        "CLEANED",
        flush=True
    )


print(
    "NEIGHBORHOOD NAME CLEANUP COMPLETE",
    flush=True
)


spark.stop()