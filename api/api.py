from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyspark.sql import SparkSession
from pyspark.sql.functions import lower, col, round, exp
from pyspark.ml.feature import BucketedRandomProjectionLSHModel

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
# NEIGHBORHOOD SIMILARITY
# ---------------------------------------------------------

neighborhood_vectors = (
    spark.read
    .parquet("data/processed/neighborhood_similarity_vectors")
    .cache()
)

neighborhood_vectors.count()

neighborhood_lsh_model = BucketedRandomProjectionLSHModel.load(
    "data/processed/neighborhood_similarity_model"
)

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

def normalize_city_name(value):
    return "".join(
        character
        for character in value.lower()
        if character.isalnum()
    )


@app.get("/api/neighborhood-available/{city}/{state}")
def neighborhood_available(city: str, state: str):

    city_key = normalize_city_name(city)
    state_key = state.strip().lower()

    return {
        "available": any(
            normalize_city_name(neighborhood["city"]) == city_key
            and neighborhood["state"].strip().lower() == state_key
            for neighborhood in neighborhood_boundaries
        )
    }


@app.get("/api/neighborhood-boundaries/{city}/{state}")
def get_neighborhood_boundaries(city: str, state: str):

    city_key = normalize_city_name(city)
    state_key = state.strip().lower()

    results = [
        neighborhood
        for neighborhood in neighborhood_boundaries
        if normalize_city_name(neighborhood["city"]) == city_key
        and neighborhood["state"].strip().lower() == state_key
    ]

    return {
        "results": results
    }

# ---------------------------------------------------------
# NEIGHBORHOOD DATA
# ---------------------------------------------------------

neighborhood_cityscope = (
    spark.read
    .parquet("data/processed/neighborhood_cityscope")
    .cache()
)

neighborhood_cityscope.count()


@app.get("/api/neighborhood/{city}/{state}/{nbhd_id}")
def get_neighborhood(
    city: str,
    state: str,
    nbhd_id: float
):
    result = (
        neighborhood_cityscope
        .filter(
            (lower(col("city")) == city.strip().lower()) &
            (lower(col("state")) == state.strip().lower()) &
            (col("nbhd_id") == nbhd_id)
        )
        .limit(1)
        .collect()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Neighborhood not found"
        )

    return result[0].asDict()

# ---------------------------------------------------------
# NEIGHBORHOOD SIMILARITY
# ---------------------------------------------------------

@app.get("/api/neighborhood-similar")
def get_neighborhood_similar(
    city: str,
    neighborhood: str
):
    city_key = city.strip().lower()
    neighborhood_key = neighborhood.strip().lower()

    query = (
        neighborhood_vectors
        .filter(
            (lower(col("city")) == city_key) &
            (lower(col("nbhd_name")) == neighborhood_key)
        )
        .limit(1)
    )

    if query.count() == 0:
        raise HTTPException(
            status_code=404,
            detail="Neighborhood not found"
        )

    query_row = query.collect()[0]

    query_vector = query_row["features"]
    query_id = query_row["nbhd_id"]
    query_state = query_row["state"]

    valid_names = (
        col("nbhd_name").isNotNull() &
        (col("nbhd_name") != "") &
        col("nbhd_name").rlike(".{2,}") &
        ~col("nbhd_name").rlike("(?i)https?://") &
        ~col("nbhd_name").rlike("^[0-9]+$")
    )

    same_city_candidates = (
        neighborhood_vectors
        .filter(
            (lower(col("city")) == city_key) &
            (col("state") == query_state)
        )
        .filter(valid_names)
    )

    same_city = (
        neighborhood_lsh_model
        .approxNearestNeighbors(
            same_city_candidates,
            query_vector,
            10
        )
        .filter(
            ~(
                (col("nbhd_id") == query_id) &
                (lower(col("nbhd_name")) == neighborhood_key)
            )
        )
        .orderBy("distCol")
        .limit(3)
        .withColumn(
            "match_score",
            round(10 * exp(-col("distCol") / 5), 1)
        )
    )

    other_city_candidates = (
        neighborhood_vectors
        .filter(
            ~(
                (lower(col("city")) == city_key) &
                (col("state") == query_state)
            )
        )
        .filter(valid_names)
    )

    other_cities = (
        neighborhood_lsh_model
        .approxNearestNeighbors(
            other_city_candidates,
            query_vector,
            100
        )
        .orderBy("distCol")
        .limit(3)
        .withColumn(
            "match_score",
            round(10 * exp(-col("distCol") / 5), 1)
        )
    )

    def format_results(df):
        return [
            {
                "city": row["city"],
                "state": row["state"],
                "nbhd_name": row["nbhd_name"],
                "nbhd_id": row["nbhd_id"],
                "match_score": row["match_score"]
            }
            for row in df.collect()
        ]

    return {
        "same_city": format_results(same_city),
        "other_cities": format_results(other_cities)
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


def point_in_ring(longitude, latitude, ring):
    inside = False
    j = len(ring) - 1

    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]

        crosses = (
            (yi > latitude) != (yj > latitude)
            and longitude < (
                (xj - xi) * (latitude - yi)
                / ((yj - yi) or 1e-12)
                + xi
            )
        )

        if crosses:
            inside = not inside

        j = i

    return inside


def point_in_polygon(longitude, latitude, polygon):
    if not polygon or not point_in_ring(longitude, latitude, polygon[0]):
        return False

    # Exclude polygon holes.
    for hole in polygon[1:]:
        if point_in_ring(longitude, latitude, hole):
            return False

    return True


def point_in_geometry(longitude, latitude, geometry):
    if not geometry:
        return False

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Feature":
        return point_in_geometry(
            longitude,
            latitude,
            geometry.get("geometry")
        )

    if geometry_type == "Polygon":
        return point_in_polygon(longitude, latitude, coordinates)

    if geometry_type == "MultiPolygon":
        return any(
            point_in_polygon(longitude, latitude, polygon)
            for polygon in coordinates
        )

    return False

def self_safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

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

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    if scope_type == "city":
        if len(scope_id) != 7:
            raise HTTPException(
                status_code=400,
                detail="Invalid city scope"
            )

        state = STATE_FIPS.get(scope_id[:2])

        if state is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid city scope"
            )

        results = poi_detail.filter(
            (col("state") == state)
            & (col("place_GEOID") == scope_id)
        )

    elif scope_type == "neighborhood":
        parts = scope_id.split("~")

        if len(parts) != 3:
            raise HTTPException(
                status_code=400,
                detail="Neighborhood scope must be city~state~nbhd_id"
            )

        city_name, state_name, nbhd_id = parts

        try:
            requested_nbhd_id = float(nbhd_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid neighborhood ID"
            )

        city_key = normalize_city_name(city_name)
        state_key = state_name.strip().lower()

        boundary = next(
            (
                item for item in neighborhood_boundaries
                if normalize_city_name(item.get("city", "")) == city_key
                and item.get("state", "").strip().lower() == state_key
                and self_safe_float(item.get("nbhd_id")) == requested_nbhd_id
            ),
            None
        )

        if boundary is None:
            raise HTTPException(
                status_code=404,
                detail="Neighborhood boundary not found"
            )

        geometry_value = boundary.get("geojson")

        try:
            geometry = (
                json.loads(geometry_value)
                if isinstance(geometry_value, str)
                else geometry_value
            )
        except (TypeError, json.JSONDecodeError):
            raise HTTPException(
                status_code=500,
                detail="Invalid neighborhood geometry"
            )

        city_rows = (
            cities
            .filter(lower(col("state")) == state_key)
            .select("city", "place_GEOID")
            .collect()
        )

        city_row = next(
            (
                row for row in city_rows
                if normalize_city_name(row["city"]) == city_key
            ),
            None
        )

        if city_row is None:
            raise HTTPException(
                status_code=404,
                detail="City not found"
            )

        place_geoid = city_row["place_GEOID"]
        poi_state = STATE_FIPS.get(place_geoid[:2])

        if poi_state is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid city state"
            )

        candidates = (
            poi_detail
            .filter(
                (col("state") == poi_state)
                & (col("place_GEOID") == place_geoid)
                & col("longitude").isNotNull()
                & col("latitude").isNotNull()
                & col("name").isNotNull()
            )
        )

        if category:
            candidates = candidates.filter(
                lower(col("cityscope_category")) == category
            )

        if search:
            candidates = candidates.filter(
                lower(col("name")).contains(search)
            )

        if starts_with:
            candidates = candidates.filter(
                lower(col("name")).startswith(starts_with)
            )

        matching_rows = []

        for row in candidates.select(
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
        ).toLocalIterator():
            poi = row.asDict()

            try:
                longitude = float(poi["longitude"])
                latitude = float(poi["latitude"])
            except (TypeError, ValueError):
                continue

            if point_in_geometry(longitude, latitude, geometry):
                matching_rows.append(poi)

        matching_rows.sort(
            key=lambda poi: (
                (poi.get("name") or "").lower(),
                str(poi.get("id") or "")
            )
        )

        page = matching_rows[offset:offset + limit]

        return {
            "results": page,
            "has_more": offset + limit < len(matching_rows)
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported POI scope"
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

    rows = (
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
        .orderBy(lower(col("name")), col("id"))
        .limit(offset + limit + 1)
        .collect()
    )

    rows = rows[offset:]
    has_more = len(rows) > limit

    if has_more:
        rows = rows[:limit]

    return {
        "results": [row.asDict() for row in rows],
        "has_more": has_more
    }
