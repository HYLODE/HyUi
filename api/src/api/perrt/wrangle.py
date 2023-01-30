"""
Data WraNGling functions
Use `_` prefix to indicate private methods
"""

# TODO: update to pandas where
# https://github.com/pandas-dev/pandas/blob/v1.4.3/pandas/core/frame.py#L10948-L10961

import numpy as np
import pandas as pd
import warnings

# use tuples (immutable) to store these data to avoid unintentional copies
_model_cols = (
    "visit_observation_id",
    "hospital_visit_id",
    "encounter",
    "observation_datetime",
    "id_in_application",
    "value_as_real",
    "value_as_text",
    "unit",
)

# columns that change per patient not per observation
# used to define an index when wrangling
_cols_per_csn = (
    "hospital_visit_id",
    "encounter",
)

_obs_types = {
    10: "SpO2",
    5: "BP",
    3040109304: "air_or_o2",
    6: "Temp",
    8: "Pulse",
    9: "Resp",
    6466: "AVPU",
    28315: "NEWS_scale_1",
    28316: "NEWS_scale_2",
}


def _fahrenheit_to_celsius(
    df: pd.DataFrame, temperature_label: str = "Temp"
) -> pd.DataFrame:
    df["value"] = df["value"].mask(
        df["id_in_application"] == temperature_label, (df["value_as_real"] - 32) * 5 / 9
    )
    return df


def _air_or_o2_as_int(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NEWS air/o2 label to integer"""
    conditions = [
        (df["id_in_application"] == "air_or_o2") & (df["value_as_text"] == "Room air"),
        (df["id_in_application"] == "air_or_o2")
        & (df["value_as_text"] == "Supplemental Oxygen"),
    ]
    choices = [
        0,
        1,
    ]
    df["value"] = np.select(conditions, choices, default=df["value"])
    return df


def _avpu_as_int(df: pd.DataFrame) -> pd.DataFrame:
    conditions = [
        (df["id_in_application"] == "AVPU") & (df["value_as_text"] == "A"),
        (df["id_in_application"] == "AVPU") & (df["value_as_text"] == "C"),
        (df["id_in_application"] == "AVPU") & (df["value_as_text"] == "V"),
        (df["id_in_application"] == "AVPU") & (df["value_as_text"] == "P"),
        (df["id_in_application"] == "AVPU") & (df["value_as_text"] == "U"),
    ]
    choices = [
        0,
        1,
        2,
        3,
        4,
    ]
    df["value"] = np.select(conditions, choices, default=df["value"])
    return df


def _bp_as_int(df: pd.DataFrame, bp_label: str = "BP") -> pd.DataFrame:
    mask = df["id_in_application"] == bp_label
    df["tmp"] = pd.to_numeric(
        df[mask]["value_as_text"].str.split("/").str[0], errors="coerce"
    )
    df["value"] = np.where(mask, df["tmp"], df["value"])
    df.drop(columns=["tmp"], inplace=True)
    return df


def _news_as_int(
    df: pd.DataFrame, news_labels: list[str] = ["NEWS_scale_1", "NEWS_scale_2"]
) -> pd.DataFrame:
    for label in news_labels:
        mask = df["id_in_application"] == label
        df["tmp"] = pd.to_numeric(df[mask]["value_as_text"], errors="coerce")
        df["value"] = np.where(mask, df["tmp"], df["value"])
        df.drop(columns=["tmp"], inplace=True)
    return df


def _long_to_wide(
    df: pd.DataFrame, cols_per_csn: tuple = _cols_per_csn
) -> pd.DataFrame:
    """
    converts SQL query data (post-wrangling) into wide data for Dash
    :param      df:            { parameter_description }
    :type       df:            { type_description }
    :param      cols_per_csn:  The cols per mrn
    :type       cols_per_csn:  list
    """

    # import pdb; pdb.set_trace()
    dft = (
        df.groupby(["id_in_application", *cols_per_csn], dropna=False)
        .agg(
            max=("value", "max"),
            min=("value", "min"),
        )
        .reset_index()
    )
    dft = dft.pivot(
        index=cols_per_csn,
        columns=["id_in_application"],
    )
    # rename the cols (b/c multi-index)
    dft.columns = [f"{col[1]}_{col[0]}".lower() for col in dft.columns.tolist()]
    dft.reset_index(inplace=True)

    # sort by news score if poss
    try:
        dft.sort_values(
            ["news_scale_1_max", "news_scale_2_max"],
            ascending=False,
            inplace=True,
        )
    except KeyError as e:
        warnings.warn(
            "Unable to sort NEWS values: possibly missing "
            "news_scale_1_max or news_scale_2_max"
        )
        print(repr(e))
    # IMPORTANT data model has now changed
    return dft


def wrangle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Single function that wraps all above
    Assumes input is result of the query
    Returns wrangled output
    Note that you will often need to define a new SQLModel for validating at this stage
    """
    # check cols exist
    for col in df.columns:
        assert col in _model_cols

    # force id_in_application to integer
    df["id_in_application"] = df["id_in_application"].astype(int)

    df.replace({"id_in_application": _obs_types}, inplace=True)
    df["value"] = df["value_as_real"]
    df = _fahrenheit_to_celsius(df)
    df = _news_as_int(df)
    df = _bp_as_int(df)
    df = _air_or_o2_as_int(df)
    df = _avpu_as_int(df)
    dft = _long_to_wide(df)
    return dft
