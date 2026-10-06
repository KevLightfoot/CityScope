import glob
import os
import subprocess

import pandas as pd


rds_dir = "data/raw/neighborhoods/rds"
output_dir = "data/processed/neighborhood_demographics"

os.makedirs(output_dir, exist_ok=True)


# Find the 147 RDS files that correspond to our 147 CDNB
# neighborhood boundary datasets.
shapefiles = sorted(
    glob.glob(
        "data/raw/neighborhoods/cdnd_data/*_onm_cleaned.shp"
    )
)

rds_files = []

for shapefile in shapefiles:

    base = os.path.basename(shapefile).replace(
        "_onm_cleaned.shp",
        ""
    )

    rds_file = f"{rds_dir}/{base}.rds"

    if os.path.exists(rds_file):
        rds_files.append(rds_file)
    else:
        print("MISSING RDS:", base)

rds_files = sorted(rds_files)

print("RDS FILES:", len(rds_files))


state_map = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia"
}


all_data = []

for rds_file in rds_files:

    filename = os.path.basename(rds_file)
    city_state = filename.replace(".rds", "")

    print("READING:", city_state)

    r_script = f"""
x <- readRDS("{rds_file}")

df <- as.data.frame(x)

if ("geometry" %in% names(df)) {{
    df$geometry <- NULL
}}

keep <- c(
    "nbhd_id",
    "nbhd_name",
    "pop",
    "pop_white",
    "pop_black",
    "pop_hisp",
    "pop_aian",
    "pop_asian",
    "pop_nhpi",
    "pop_other",
    "pop_two"
)

df <- df[, intersect(keep, names(df)), drop = FALSE]

write.csv(
    df,
    "{output_dir}/{city_state}.csv",
    row.names = FALSE
)
"""

    subprocess.run(
        ["Rscript", "-e", r_script],
        check=True
    )


# Read and aggregate each city's demographic data.
csv_files = sorted(
    glob.glob(f"{output_dir}/*.csv")
)

for csv_file in csv_files:

    filename = os.path.basename(csv_file)
    city_state = filename.replace(".csv", "")

    df = pd.read_csv(csv_file)

    if "pop" not in df.columns or "nbhd_id" not in df.columns:
        continue

    state_abbr = city_state[-2:]
    city = city_state[:-2]

    df["city"] = city
    df["state_abbr"] = state_abbr
    df["state"] = state_map.get(state_abbr)

    numeric_columns = [
        "pop",
        "pop_white",
        "pop_black",
        "pop_hisp",
        "pop_aian",
        "pop_asian",
        "pop_nhpi",
        "pop_other",
        "pop_two"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Aggregate tract/block records into one row per CDNB neighborhood.
    grouped = (
        df.groupby(
            [
                "city",
                "state",
                "state_abbr",
                "nbhd_id",
                "nbhd_name"
            ],
            dropna=False
        )[numeric_columns]
        .sum()
        .reset_index()
    )

    all_data.append(grouped)


demographics = pd.concat(
    all_data,
    ignore_index=True
)


# Remove rows without a neighborhood name.
demographics = demographics[
    demographics["nbhd_name"].notna()
].copy()


# Calculate race/ethnicity percentages.
population = demographics["pop"].replace(0, pd.NA)

demographics["white_pct"] = (
    demographics["pop_white"] / population * 100
)

demographics["black_pct"] = (
    demographics["pop_black"] / population * 100
)

demographics["hisp_pct"] = (
    demographics["pop_hisp"] / population * 100
)

demographics["aian_pct"] = (
    demographics["pop_aian"] / population * 100
)

demographics["asian_pct"] = (
    demographics["pop_asian"] / population * 100
)

demographics["nhpi_pct"] = (
    demographics["pop_nhpi"] / population * 100
)

demographics["other_pct"] = (
    demographics["pop_other"] / population * 100
)

demographics["two_pct"] = (
    demographics["pop_two"] / population * 100
)


# Save the final one-row-per-neighborhood dataset.
demographics.to_parquet(
    f"{output_dir}/neighborhood_demographics.parquet",
    index=False
)


print()
print("ROWS:", len(demographics))
print("CITIES:", demographics["city"].nunique())
print("STATES:", demographics["state"].nunique())
print(
    "NEIGHBORHOODS:",
    demographics["nbhd_name"].nunique()
)