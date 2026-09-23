"""
weather_aggregate.py takes weather observations from weather_clean and creates monthly weather observations 
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, count, year, month, when

# Create Spark Session
spark = (
    SparkSession.builder.appName("CityScope Weather Aggregation")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

weather_df = (spark.read.parquet("data/processed/weather_observations"))

weather_year_and_month = (
    weather_df
    .withColumn("year", year(col("date")))
    .withColumn("month", month(col("date")))
)

weather_grouped = (
    weather_year_and_month.groupBy("station_id", "year", "month")
)

weather_aggregated = (
    weather_grouped.agg(
        avg(
            when(
                col("element") == "TMIN",
                col("temperature_f")
            )
        ).alias("avg_low"),

        avg(
            when(
                col("element") == "TAVG",
                col("temperature_f")
            )
        ).alias("avg_temp"),

        avg(
            when(
                col("element") == "TMAX",
                col("temperature_f")
            )
        ).alias("avg_high"),

        max(
            when(
                col("element") == "TMAX",
                col("temperature_f")
            )
        ).alias("high"),

        min(
            when(
                col("element") == "TMIN",
                col("temperature_f")
            )
        ).alias("low"),

        count("temperature_f").alias("observation_count")
    )
 )

weather_aggregated.show(15, truncate=False)