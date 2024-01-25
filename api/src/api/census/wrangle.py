import numpy as np
import pandas as pd
import warnings


def _split_location_string(df: pd.DataFrame) -> pd.DataFrame:
    """
    Splits a location string into dept/room/bed
    """
    split_locations_df = (
        df["location_string"]
        .str.split("^", expand=True)
        .rename(columns={0: "dept", 1: "room", 2: "bed"})
    )
    return pd.concat((df, split_locations_df), axis="columns")


def _remove_non_beds(
    df: pd.DataFrame, non_beds: tuple[str, ...] = ("null", "wait", "proc rm")
) -> pd.DataFrame:
    """
    Removes non beds e.g. null, wait
    """
    mask = df["bed"].str.lower().isin(non_beds)
    return df[~mask]


def _aggregate_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregation from location (bed) level to ward level
    Generates estimates of beds likely to be closed
    """
    df["cvl_discharge"] = pd.to_datetime(df["cvl_discharge"], errors="coerce", utc=True)
    if df["modified_at"].dt.tz is None:
        df["modified_at"] = df["modified_at"].dt.tz_localize("UTC")
        warnings.warn("[WARN] Forcing timezone to UTC for 'modified_at'")

    groups = df.groupby("department")
    # aggregate by dept
    res = groups.agg(
        beds=("location_id", "count"),
        patients=("occupied", "sum"),
        days_since_last_dc=("cvl_discharge", lambda x: x.max(skipna=True)),
        modified_at=("modified_at", "max"),
    )

    # calculate additional numbers
    res["empties"] = res["beds"] - res["patients"]
    # calculate opens on the front end since this requires a separate data
    # source
    # placeholder: need to subtract closed from empties
    # res["opens"] = res["empties"]

    # Calculate days since last discharge, but handle NaT values in wards by allowing
    # the quantity to be a float rather than integer
    res["days_since_last_dc"] = (
        (res["modified_at"] - res["days_since_last_dc"]).dt.floor("d").dt.days
    )
    # Convert remaining NaT values to -999, then convert the Series dtype to int
    res["days_since_last_dc"] = (
        res["days_since_last_dc"].replace(np.nan, -999.0).astype(int)
    )

    # use days since last dc and there being no patients to define if a ward
    # appears to be closed defined closed: temp and perm
    res["closed_temp"] = pd.DataFrame(
        [
            res["days_since_last_dc"] > 2,
            res["days_since_last_dc"] <= 30,
            res["patients"] == 0,
        ]
    ).T.all(axis="columns")

    def _closed_perm_conditions(row: pd.Series) -> bool:
        """Calculate permanent closure conditions.

        Handles NaT values of days_since_last_dc, which are
        converted to -999.

        Args:
            row (pd.Series): Pandas DataFrame row

        Returns:
            bool: Is the ward permanently closed?
        """
        if row["days_since_last_dc"] > 30 and row["patients"] == 0:
            closed = True
        elif row["days_since_last_dc"] < 0:
            closed = True
        else:
            closed = False
        return closed

    res["closed_perm"] = res.apply(_closed_perm_conditions, axis=1)

    # drop closed perm
    # mask = ~res["closed_perm"]
    # res = res[mask]

    res = res[
        [
            "beds",
            "patients",
            "empties",
            "days_since_last_dc",
            "closed_temp",
            "closed_perm",
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
    return _aggregate_by_department(df)
