"""
api.py provides the CityScope API for city search,
city data, and city boundary geometry
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyspark.sql import SparkSession
from pyspark.sql.functions import lower, col


app = FastAPI(title="CityScope API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create Spark session
spark = (
    SparkSession.builder
    .appName("CityScope API")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


# Read processed city data
cities = (
    spark.read
    .parquet("data/processed/cityscope_city")
    .cache()
)

cities.count()


# Read processed place boundaries
boundaries = (
    spark.read
    .parquet("data/processed/place_boundaries")
    .cache()
)

boundaries.count()


@app.get("/api/cities")
def search_cities(q: str = ""):
    q = q.strip()

    if not q:
        return []

    results = (
        cities
        .filter(
            lower(col("city")).contains(q.lower())
        )
        .select(
            "city",
            "state"
        )
        .dropDuplicates()
        .orderBy("city", "state")
        .collect()
    )

    return [
        {
            "city": row["city"],
            "state": row["state"]
        }
        for row in results
    ]


@app.get("/api/city/{city}/{state}")
def get_city(city: str, state: str):
    result = (
        cities
        .filter(
            (lower(col("city")) == city.lower()) &
            (lower(col("state")) == state.lower())
        )
        .limit(1)
        .collect()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="City not found"
        )

    return result[0].asDict()


@app.get("/api/boundary/{place_geoid}")
def get_boundary(place_geoid: str):
    result = (
        boundaries
        .filter(col("GEOID") == place_geoid)
        .select(
            "GEOID",
            "NAME",
            "NAMELSAD",
            "geojson"
        )
        .limit(1)
        .collect()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Boundary not found"
        )

    row = result[0]

    return {
        "GEOID": row["GEOID"],
        "NAME": row["NAME"],
        "NAMELSAD": row["NAMELSAD"],
        "geojson": row["geojson"]
    }