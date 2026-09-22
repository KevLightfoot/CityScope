
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Create a local Spark session for development.
spark = (
    SparkSession.builder
    .appName("CityScope")
    .master("local[2]")
    .getOrCreate()
)

# Temporary sample data representing cities.
# This is only to verify that Spark works.
cities = [
    ("Austin", "TX", 974447, 1800),
    ("Dallas", "TX", 1304379, 1700),
    ("Denver", "CO", 713252, 2100),
    ("Omaha", "NE", 486051, 1300),
]

columns = [
    "city",
    "state",
    "population",
    "monthly_rent"
]

df = spark.createDataFrame(cities, columns)

print("CityScope Spark test")
print("Number of cities:", df.count())

# A real Spark transformation.
affordable_cities = df.filter(col("monthly_rent") < 1900)

affordable_cities.show()

spark.stop()