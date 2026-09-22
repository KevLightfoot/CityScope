from sedona.spark import SedonaContext

spark = (
    SedonaContext.builder()
    .appName("CityScope Sedona Test")
    .master("local[2]")
    .config(
        "spark.jars.packages",
        "org.apache.sedona:sedona-spark-4.1_2.13:1.9.1,"
        "org.datasyslab:geotools-wrapper:1.9.1-33.5"
    )
    .getOrCreate()
)

sedona = SedonaContext.create(spark)

print("Sedona successfully connected to Spark!")

spark.stop()