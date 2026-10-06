from pyspark.sql.functions import col, when, input_file_name, regexp_extract
from sedona.spark import SedonaContext


# Create a local Spark session using 4 worker threads.
spark = (
    SedonaContext.builder()
    .appName("CityScope Neighborhood Cleaning")
    .master("local[4]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.0_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# Initialize Sedona
sedona = SedonaContext.create(spark)

# Read nationwide city-defined neighborhood shapefiles
neighborhoods = (
    spark.read
    .format("shapefile")
    .load("data/raw/neighborhoods/cdnd_data/*_onm_cleaned.shp")
)


# Add source filename so city and state can be derived
neighborhoods = neighborhoods.withColumn(
    "source_file",
    input_file_name()
)


# Extract city/state from filenames such as:
# AustinTX_onm_cleaned.shp
neighborhoods = neighborhoods.withColumn(
    "city_state",
    regexp_extract(
        col("source_file"),
        r"([^/]+)_onm_cleaned\.shp$",
        1
    )
)


# Split city/state using the known two-letter state abbreviation
state_pattern = (
    r"^(.*?)(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)$"
)

neighborhoods = neighborhoods.withColumn(
    "city",
    regexp_extract(col("city_state"), state_pattern, 1)
)

neighborhoods = neighborhoods.withColumn(
    "state_abbr",
    regexp_extract(col("city_state"), state_pattern, 2)
)


mapping_expr = (
    when(col("state_abbr") == "AL", "Alabama")
    .when(col("state_abbr") == "AK", "Alaska")
    .when(col("state_abbr") == "AZ", "Arizona")
    .when(col("state_abbr") == "AR", "Arkansas")
    .when(col("state_abbr") == "CA", "California")
    .when(col("state_abbr") == "CO", "Colorado")
    .when(col("state_abbr") == "CT", "Connecticut")
    .when(col("state_abbr") == "DE", "Delaware")
    .when(col("state_abbr") == "FL", "Florida")
    .when(col("state_abbr") == "GA", "Georgia")
    .when(col("state_abbr") == "HI", "Hawaii")
    .when(col("state_abbr") == "ID", "Idaho")
    .when(col("state_abbr") == "IL", "Illinois")
    .when(col("state_abbr") == "IN", "Indiana")
    .when(col("state_abbr") == "IA", "Iowa")
    .when(col("state_abbr") == "KS", "Kansas")
    .when(col("state_abbr") == "KY", "Kentucky")
    .when(col("state_abbr") == "LA", "Louisiana")
    .when(col("state_abbr") == "ME", "Maine")
    .when(col("state_abbr") == "MD", "Maryland")
    .when(col("state_abbr") == "MA", "Massachusetts")
    .when(col("state_abbr") == "MI", "Michigan")
    .when(col("state_abbr") == "MN", "Minnesota")
    .when(col("state_abbr") == "MS", "Mississippi")
    .when(col("state_abbr") == "MO", "Missouri")
    .when(col("state_abbr") == "MT", "Montana")
    .when(col("state_abbr") == "NE", "Nebraska")
    .when(col("state_abbr") == "NV", "Nevada")
    .when(col("state_abbr") == "NH", "New Hampshire")
    .when(col("state_abbr") == "NJ", "New Jersey")
    .when(col("state_abbr") == "NM", "New Mexico")
    .when(col("state_abbr") == "NY", "New York")
    .when(col("state_abbr") == "NC", "North Carolina")
    .when(col("state_abbr") == "ND", "North Dakota")
    .when(col("state_abbr") == "OH", "Ohio")
    .when(col("state_abbr") == "OK", "Oklahoma")
    .when(col("state_abbr") == "OR", "Oregon")
    .when(col("state_abbr") == "PA", "Pennsylvania")
    .when(col("state_abbr") == "RI", "Rhode Island")
    .when(col("state_abbr") == "SC", "South Carolina")
    .when(col("state_abbr") == "SD", "South Dakota")
    .when(col("state_abbr") == "TN", "Tennessee")
    .when(col("state_abbr") == "TX", "Texas")
    .when(col("state_abbr") == "UT", "Utah")
    .when(col("state_abbr") == "VT", "Vermont")
    .when(col("state_abbr") == "VA", "Virginia")
    .when(col("state_abbr") == "WA", "Washington")
    .when(col("state_abbr") == "WV", "West Virginia")
    .when(col("state_abbr") == "WI", "Wisconsin")
    .when(col("state_abbr") == "WY", "Wyoming")
    .when(col("state_abbr") == "DC", "District of Columbia")
)

neighborhoods = neighborhoods.withColumn(
    "state",
    mapping_expr
)


# Select final neighborhood fields
neighborhoods = neighborhoods.select(
    col("city"),
    col("state"),
    col("state_abbr"),
    col("nbhd").alias("neighborhood"),
    col("geometry")
)


# Remove records without neighborhood names or geometry
neighborhoods = neighborhoods.filter(
    col("neighborhood").isNotNull() &
    col("geometry").isNotNull()
)


# Save cleaned neighborhood boundaries
neighborhoods.write.mode("overwrite").parquet(
    "data/processed/neighborhoods"
)

spark.stop()