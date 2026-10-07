"""
state_utils.py provides shared state normalization functions
for CityScope datasets.
"""

from pyspark.sql.functions import col, create_map, lit, lower, trim


def add_state_key(df, state_column="state"):
    """
    Adds a state_key column that converts state abbreviations
    to lowercase full state names.
    """

    state_map = create_map(
        lit("al"), lit("alabama"),
        lit("ak"), lit("alaska"),
        lit("az"), lit("arizona"),
        lit("ar"), lit("arkansas"),
        lit("ca"), lit("california"),
        lit("co"), lit("colorado"),
        lit("ct"), lit("connecticut"),
        lit("de"), lit("delaware"),
        lit("dc"), lit("district of columbia"),
        lit("fl"), lit("florida"),
        lit("ga"), lit("georgia"),
        lit("hi"), lit("hawaii"),
        lit("id"), lit("idaho"),
        lit("il"), lit("illinois"),
        lit("in"), lit("indiana"),
        lit("ia"), lit("iowa"),
        lit("ks"), lit("kansas"),
        lit("ky"), lit("kentucky"),
        lit("la"), lit("louisiana"),
        lit("me"), lit("maine"),
        lit("md"), lit("maryland"),
        lit("ma"), lit("massachusetts"),
        lit("mi"), lit("michigan"),
        lit("mn"), lit("minnesota"),
        lit("ms"), lit("mississippi"),
        lit("mo"), lit("missouri"),
        lit("mt"), lit("montana"),
        lit("ne"), lit("nebraska"),
        lit("nv"), lit("nevada"),
        lit("nh"), lit("new hampshire"),
        lit("nj"), lit("new jersey"),
        lit("nm"), lit("new mexico"),
        lit("ny"), lit("new york"),
        lit("nc"), lit("north carolina"),
        lit("nd"), lit("north dakota"),
        lit("oh"), lit("ohio"),
        lit("ok"), lit("oklahoma"),
        lit("or"), lit("oregon"),
        lit("pa"), lit("pennsylvania"),
        lit("ri"), lit("rhode island"),
        lit("sc"), lit("south carolina"),
        lit("sd"), lit("south dakota"),
        lit("tn"), lit("tennessee"),
        lit("tx"), lit("texas"),
        lit("ut"), lit("utah"),
        lit("vt"), lit("vermont"),
        lit("va"), lit("virginia"),
        lit("wa"), lit("washington"),
        lit("wv"), lit("west virginia"),
        lit("wi"), lit("wisconsin"),
        lit("wy"), lit("wyoming")
    )

    return df.withColumn(
        "state_key",
        state_map[lower(trim(col(state_column)))]
    )