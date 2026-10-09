from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyspark.sql import SparkSession
from pyspark.sql.functions import lower, col
import json

app = FastAPI(title="CityScope API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

spark = (
    SparkSession.builder
    .appName("CityScope API")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


# ---------------------------------------------------------
# CITY DATA
# ---------------------------------------------------------

cities = (
    spark.read
    .parquet("data/processed/cityscope_city")
    .cache()
)

cities.count()


# ---------------------------------------------------------
# CITY AND NBHD BOUNDARY DATA
# ---------------------------------------------------------

boundaries = (
    spark.read
    .parquet("data/processed/place_boundaries")
    .cache()
)

boundaries.count()

with open(
    "data/processed/neighborhood_boundaries.json",
    "r"
) as f:
    neighborhood_boundaries = json.load(f)


# ---------------------------------------------------------
# WEATHER DATA
# ---------------------------------------------------------

weather_monthly = (
    spark.read
    .parquet("data/processed/weather_monthly")
    .cache()
)

weather_monthly.count()


# ---------------------------------------------------------
# HOUSING PROPERTY DATA
# ---------------------------------------------------------

housing_properties = (
    spark.read
    .parquet("data/processed/housing_city_properties")
)


# ---------------------------------------------------------
# Read individual POI detail data
# ---------------------------------------------------------
poi_detail = (
    spark.read
    .parquet("data/processed/poi_detail")
)


STATE_FIPS = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY"
}


# ---------------------------------------------------------
# CITY SEARCH
# ---------------------------------------------------------

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
        .select("city", "state")
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


# ---------------------------------------------------------
# CITY DATA
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# CITY BOUNDARY
# ---------------------------------------------------------

@app.get("/api/boundary/{geoid}")
def get_boundary(geoid: str):

    result = (
        boundaries
        .filter(col("GEOID") == geoid)
        .limit(1)
        .collect()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Boundary not found"
        )

    return result[0].asDict()

# ---------------------------------------------------------
# NBHD BOUNDARY
# ---------------------------------------------------------

@app.get("/api/neighborhood-boundaries/{city}/{state}")
def get_neighborhood_boundaries(city: str, state: str):
    city_key = city.strip().lower()
    state_key = state.strip().lower()

    results = [
        neighborhood
        for neighborhood in neighborhood_boundaries
        if neighborhood["city"].strip().lower() == city_key
        and neighborhood["state"].strip().lower() == state_key
    ]

    return {
        "results": results
    }

# ---------------------------------------------------------
# WEATHER
# ---------------------------------------------------------

@app.get("/api/weather/{geoid}")
def get_weather(geoid: str):
    result = (
        weather_monthly
        .filter(
            col("place_GEOID") == geoid
        )
        .select(
            "month",
            "avg_temp",
            "avg_low",
            "avg_high"
        )
        .orderBy("month")
        .collect()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Weather data not found"
        )

    monthly = [
        {
            "month": row["month"],
            "avg_temp": row["avg_temp"],
            "avg_low": row["avg_low"],
            "avg_high": row["avg_high"]
        }
        for row in result
    ]

    seasons = {
        "Winter": [12, 1, 2],
        "Spring": [3, 4, 5],
        "Summer": [6, 7, 8],
        "Fall": [9, 10, 11]
    }

    seasonal = []

    for season, months in seasons.items():
        rows = [
            row
            for row in monthly
            if row["month"] in months
        ]

        if not rows:
            continue

        def average(field):
            values = [
                row[field]
                for row in rows
                if row[field] is not None
            ]

            if not values:
                return None

            return sum(values) / len(values)

        seasonal.append({
            "season": season,
            "avg_temp": average("avg_temp"),
            "avg_low": average("avg_low"),
            "avg_high": average("avg_high")
        })

    return {
        "monthly": monthly,
        "seasonal": seasonal
    }


# ---------------------------------------------------------
# HOUSING PROPERTIES
# ---------------------------------------------------------

@app.get("/api/housing/{city}/{state}")
def get_housing(city: str, state: str):
    city_key = city.strip().lower()
    state_key = state.strip().lower()

    result = (
        housing_properties
        .filter(
            (col("city_key") == city_key) &
            (col("state_key") == state_key)
        )
        .select(
            "id",
            "street",
            "unit",
            "city",
            "state",
            "zip",
            "lat",
            "lng",
            "property_type",
            "beds",
            "baths",
            "sqft",
            "lot_sqft",
            "year_built",
            "status",
            "list_price"
        )
        .collect()
    )

    return [
        row.asDict()
        for row in result
    ]

@app.get("/api/pois/{scope_type}/{scope_id}")
def get_pois(
    scope_type: str,
    scope_id: str,
    category: str = "",
    search: str = "",
    starts_with: str = "",
    limit: int = 50,
    offset: int = 0
):
    scope_type = scope_type.lower().strip()
    category = category.lower().strip()
    search = search.lower().strip()
    starts_with = starts_with.lower().strip()

    if scope_type != "city":
        raise HTTPException(
            status_code=400,
            detail="Unsupported POI scope"
        )

    if len(scope_id) != 7:
        raise HTTPException(
            status_code=400,
            detail="Invalid city scope"
        )

    state_fips = scope_id[:2]
    state = STATE_FIPS.get(state_fips)

    if state is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid city scope"
        )

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    results = (
        poi_detail
        .filter(
            (col("state") == state) &
            (col("place_GEOID") == scope_id)
        )
    )

    if category:
        results = results.filter(
            lower(col("cityscope_category")) == category
        )

    if search:
        results = results.filter(
            lower(col("name")).contains(search)
        )

    if starts_with:
        results = results.filter(
            lower(col("name")).startswith(starts_with)
        )


    results = (
        results
        .filter(col("name").isNotNull())
        .select(
            "id",
            "name",
            "cityscope_category",
            "category",
            "basic_category",
            "confidence",
            "place_GEOID",
            "place_name",
            "state",
            "longitude",
            "latitude"
        )
        .orderBy(
            lower(col("name")),
            col("id")
        )
        .limit(offset + limit + 1)
        .collect()
    )

    results = results[offset:]

    has_more = len(results) > limit

    if has_more:
        results = results[:limit]

    return {
        "results": [
            row.asDict()
            for row in results
        ],
        "has_more": has_more
    }
