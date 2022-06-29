# src/utils/perrt/wng.py
"""
Data WraNGling functions
Use `_` prefix to indicate private methods
"""

# TODO: update to pandas where
# https://github.com/pandas-dev/pandas/blob/v1.4.3/pandas/core/frame.py#L10948-L10961

import numpy as np
import pandas as pd

_model_cols = [
    "visit_observation_id",
    "date_of_birth",
    "lastname",
    "firstname",
    "mrn",
    "ob_tail_i",
    "observation_datetime",
    "id_in_application",
    "value_as_real",
    "value_as_text",
    "unit",
    "sex",
    "bed_admit_dt",
    "dept_name",
    "room_name",
    "bed_hl7",
    "perrt_consult_datetime",
    "Perrt_id",
]

# columns that change per patient not per observation
# used to define an index when wrangling
_cols_per_mrn = [
    "date_of_birth",
    "lastname",
    "firstname",
    "mrn",
    "sex",
    "bed_admit_dt",
    "dept_name",
    "room_name",
    "bed_hl7",
    "perrt_consult_datetime",
]

_obs_types = dict(
    SpO2="10",
    BP="5",
    air_or_o2="3040109304",
    Temp="6",
    Pulse="8",
    Resp="9",
    AVPU="6466",
    NEWS_scale_1="28315",
    NEWS_scale_2="28316",
)

_obs_types_inverse = {v: k for k, v in _obs_types.items()}


def _fahrenheit_to_celsius(df, temperature_label: str = "Temp"):
    df["value"] = df["value"].mask(
        df["id_in_application"] == temperature_label, (df["value_as_real"] - 32) * 5 / 9
    )
    return df


def _air_or_o2_as_int(df):
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


def _avpu_as_int(df):
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


def _bp_as_int(df, bp_label: str = "BP"):
    mask = df["id_in_application"] == bp_label
    df["tmp"] = pd.to_numeric(
        df[mask]["value_as_text"].str.split("/").str[0], errors="coerce"
    )
    df["value"] = np.where(mask, df["tmp"], df["value"])
    df.drop(columns=["tmp"], inplace=True)
    return df


def _news_as_int(df, news_labels: list[str] = ["NEWS_scale_1", "NEWS_scale_2"]):
    for label in news_labels:
        mask = df["id_in_application"] == label
        df["tmp"] = pd.to_numeric(df[mask]["value_as_text"], errors="coerce")
        df["value"] = np.where(mask, df["tmp"], df["value"])
        df.drop(columns=["tmp"], inplace=True)
    return df


def _long_to_wide(df, cols_per_mrn: list = _cols_per_mrn) -> pd.DataFrame:
    """
    converts SQL query data (post-wrangling) into wide data for Dash
    :param      df:            { parameter_description }
    :type       df:            { type_description }
    :param      cols_per_mrn:  The cols per mrn
    :type       cols_per_mrn:  list
    """

    dft = (
        df.groupby(["id_in_application", *cols_per_mrn])
        .agg(
            max=("value", "max"),
            min=("value", "min"),
        )
        .reset_index()
    )
    dft = dft.pivot(
        index=cols_per_mrn,
        columns=["id_in_application"],
    )
    # rename the cols (b/c multi-index)
    dft.columns = [f"{col[1]}_{col[0]}".lower() for col in dft.columns.tolist()]
    dft.reset_index(inplace=True)
    dft.sort_values(
        ["news_scale_1_max", "news_scale_2_max"],
        ascending=False,
        inplace=True,
    )
    # IMPORTANT data model has now changed
    return dft


def wrangle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Single function that wraps all above
    Assumes input is result of the query
    Returns wrangled output
    Note that you will often need to define a new SQLModel for validating at this stage
    """
    # TODO: error checking / at the v least check the columns exist
    for col in df.columns:
        assert col in _model_cols
    try:
        df.replace({"id_in_application": _obs_types_inverse}, inplace=True)
    except TypeError:
        df["id_in_application"] = df["id_in_application"].astype(str)
        df.replace({"id_in_application": _obs_types_inverse}, inplace=True)
    df["value"] = df["value_as_real"]
    df = _fahrenheit_to_celsius(df)
    df = _news_as_int(df)
    df = _bp_as_int(df)
    df = _air_or_o2_as_int(df)
    df = _avpu_as_int(df)
    dft = _long_to_wide(df)
    return dft
