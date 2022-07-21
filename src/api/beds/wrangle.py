from typing import List

import pandas as pd


def _split_location_string(df: pd.DataFrame) -> pd.DataFrame:
    """
    Splits a location string into dept/room/bed
    """
    temp = (
        df["location_string"]
        .str.split("^", expand=True)
        .rename(columns={0: "dept", 1: "room", 2: "bed"})
    )
    for s in ["dept", "room", "bed"]:
        df[s] = temp[s]
    return df


def _remove_non_beds(
    df: pd.DataFrame, nonbeds: List[str] = ["null", "wait"]
) -> pd.DataFrame:
    """
    Removes non beds e.g. null, wait
    """
    mask = df["bed"].str.lower().isin(nonbeds)
    df = df[~mask]
    return df


def _aggregate_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregation from location (bed) level to ward level
    """
    df["cvl_discharge"] = pd.to_datetime(df["cvl_discharge"], errors="coerce", utc=True) 
    groups = df.groupby("department")
    # aggregate by dept
    res = groups.agg(
        beds=("location_id", "count"),
        patients=("occupied", "sum"),
        last_dc=("cvl_discharge", lambda x: x.max(skipna=True)),
        modified_at=("modified_at", "max"),
    )
    # calculate additional numbers
    res["empties"] = res["beds"] - res["patients"]
    res["opens"] = res["empties"]  # place holder : need to subtract closed from empties
    res["last_dc"] = (
        (res["modified_at"] - res["last_dc"])
        .apply(lambda x: pd.Timedelta.floor(x, "d"))
        .dt.days
    )

    # defined closed: temp and perm
    res["closed_temp"] = pd.DataFrame(
        [
            res["last_dc"] > 2,
            res["last_dc"] <= 30,
            res["patients"] == 0,
        ]
    ).T.all(axis="columns")

    res["closed_perm"] = pd.DataFrame(
        [
            res["last_dc"] > 30,
            res["patients"] == 0,
        ]
    ).T.all(axis="columns")

    # drop closed perm
    mask = ~res["closed_perm"]

    res = res[mask]
    res = res[
        [
            "beds",
            "patients",
            "empties",
            "opens",
            "last_dc",
            "closed_temp",
            "modified_at",
        ]
    ]
    res.reset_index(inplace=True)
    return res


def aggregate_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregation from location (bed) level to ward level
    Wrapper function
    """
    df = _split_location_string(df)
    df = _remove_non_beds(df)
    df = _aggregate_by_department(df)
    return df
