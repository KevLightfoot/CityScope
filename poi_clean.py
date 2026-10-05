import duckdb
import os

RELEASE = "2026-09-23.1"
OUTPUT = "data/processed/poi"

os.makedirs(OUTPUT, exist_ok=True)

con = duckdb.connect()

con.execute("INSTALL spatial;")
con.execute("LOAD spatial;")
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")
con.execute("SET s3_region = 'us-west-2';")

source = f"""
read_parquet(
    's3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*',
    filename=true,
    hive_partitioning=true
)
"""

query = f"""
COPY (
    SELECT
        id,
        names.primary AS name,
        geometry,
        confidence,
        basic_category,
        taxonomy.primary AS category,

        addresses[1].region AS state,

        CASE
            WHEN category IS NULL THEN 'other'

            WHEN
                lower(category) LIKE '%restaurant%'
                OR lower(category) LIKE '%food%'
                OR lower(category) LIKE '%bakery%'
                OR lower(category) LIKE '%cafe%'
                OR lower(category) LIKE '%coffee%'
                OR lower(category) LIKE '%bar%'
                OR lower(category) LIKE '%ice_cream%'
                OR lower(category) LIKE '%fast_food%'
                THEN 'food'

            WHEN
                lower(category) LIKE '%grocery%'
                OR lower(category) LIKE '%supermarket%'
                OR lower(category) LIKE '%convenience_store%'
                THEN 'grocery'

            WHEN
                lower(category) LIKE '%hospital%'
                OR lower(category) LIKE '%health%'
                OR lower(category) LIKE '%doctor%'
                OR lower(category) LIKE '%medical%'
                OR lower(category) LIKE '%dental%'
                OR lower(category) LIKE '%pharmacy%'
                OR lower(category) LIKE '%clinic%'
                OR lower(category) LIKE '%therapy%'
                THEN 'healthcare'

            WHEN
                lower(category) LIKE '%school%'
                OR lower(category) LIKE '%university%'
                OR lower(category) LIKE '%college%'
                OR lower(category) LIKE '%education%'
                OR lower(category) LIKE '%preschool%'
                OR lower(category) LIKE '%kindergarten%'
                THEN 'education'

            WHEN
                lower(category) LIKE '%store%'
                OR lower(category) LIKE '%shopping%'
                OR lower(category) LIKE '%retail%'
                OR lower(category) LIKE '%clothing%'
                OR lower(category) LIKE '%furniture%'
                OR lower(category) LIKE '%electronics%'
                THEN 'shopping'

            WHEN
                lower(category) LIKE '%bank%'
                OR lower(category) LIKE '%financial%'
                OR lower(category) LIKE '%insurance%'
                OR lower(category) LIKE '%atm%'
                THEN 'financial'

            WHEN
                lower(category) LIKE '%gym%'
                OR lower(category) LIKE '%fitness%'
                OR lower(category) LIKE '%yoga%'
                OR lower(category) LIKE '%martial_arts%'
                THEN 'fitness'

            WHEN
                lower(category) LIKE '%park%'
                OR lower(category) LIKE '%trail%'
                OR lower(category) LIKE '%golf%'
                OR lower(category) LIKE '%recreation%'
                OR lower(category) LIKE '%sports%'
                OR lower(category) LIKE '%swimming%'
                THEN 'recreation'

            WHEN
                lower(category) LIKE '%movie%'
                OR lower(category) LIKE '%theater%'
                OR lower(category) LIKE '%theatre%'
                OR lower(category) LIKE '%museum%'
                OR lower(category) LIKE '%music%'
                OR lower(category) LIKE '%entertainment%'
                OR lower(category) LIKE '%nightlife%'
                THEN 'entertainment'

            WHEN
                lower(category) LIKE '%gas_station%'
                OR lower(category) LIKE '%fuel%'
                OR lower(category) LIKE '%airport%'
                OR lower(category) LIKE '%bus_station%'
                OR lower(category) LIKE '%train_station%'
                OR lower(category) LIKE '%transport%'
                OR lower(category) LIKE '%ev_charging%'
                THEN 'transportation'

            WHEN
                lower(category) LIKE '%hotel%'
                OR lower(category) LIKE '%motel%'
                OR lower(category) LIKE '%resort%'
                OR lower(category) LIKE '%lodging%'
                THEN 'lodging'

            WHEN
                lower(category) LIKE '%worship%'
                OR lower(category) LIKE '%church%'
                OR lower(category) LIKE '%mosque%'
                OR lower(category) LIKE '%synagogue%'
                OR lower(category) LIKE '%temple%'
                OR lower(category) LIKE '%religious%'
                THEN 'religious'

            ELSE 'other'
        END AS cityscope_category

    FROM {source}
    WHERE addresses[1].country = 'US'
)
TO '{OUTPUT}'
(
    FORMAT PARQUET,
    COMPRESSION ZSTD,
    PARTITION_BY (state),
    OVERWRITE_OR_IGNORE TRUE
);
"""

print("Starting nationwide U.S. POI extraction...")
print("Source:", RELEASE)
print("Output:", OUTPUT)

con.execute(query)

print("POI extraction complete.")