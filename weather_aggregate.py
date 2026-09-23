"""
weather_aggregate.py aggregates cleaned weather observations into
monthly station-level climate summaries for CityScope. 
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, count, year, month, when

# Create a local Spark session using 4 worker threads.
spark = (
    SparkSession.builder.appName("CityScope Weather Aggregation")
    .master("local[4]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")


# Read the cleaned weather observations from Parquet.
weather_df = (spark.read.parquet("data/processed/weather_observations"))

# Extract year and month from each observation date for monthly aggregation.
weather_year_and_month = (
    weather_df
    .withColumn("year", year(col("date")))
    .withColumn("month", month(col("date")))
)

# Group observations by station, year, and month. 
weather_grouped = (
    weather_year_and_month.groupBy("station_id", "year", "month")
)

# Calculate monthly temperature averages, recorded extremes,
# and the number of valid temperature observations for each station.
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

# Save monthly station-level climate summaries as Parquet.
weather_aggregated.write.mode("overwrite").parquet("data/processed/weather_monthly")

spark.stop()