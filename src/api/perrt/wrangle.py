# src/utils/perrt/wng.py
"""
Data WraNGling functions
"""
import pandas as pd
import numpy as np

model_cols = [
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
]

obs_types = dict(
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

obs_types_inverse = {v: k for k, v in obs_types.items()}


def air_or_o2_as_int(df):
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


def avpu_as_int(df):
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


def bp_as_int(df, bp_label: str = "BP"):
    mask = df["id_in_application"] == bp_label
    df["tmp"] = pd.to_numeric(
        df[mask]["value_as_text"].str.split("/").str[0], errors="coerce"
    )
    df["value"] = np.where(mask, df["tmp"], df["value"])
    df.drop(columns=["tmp"], inplace=True)
    return df


def news_as_int(df, news_labels: list[str] = ["NEWS_scale_1", "NEWS_scale_2"]):
    for label in news_labels:
        mask = df["id_in_application"] == label
        df["tmp"] = pd.to_numeric(df[mask]["value_as_text"], errors="coerce")
        df["value"] = np.where(mask, df["tmp"], df["value"])
        df.drop(columns=["tmp"], inplace=True)
    return df


def wrangle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Single function that wraps all above
    Assumes input is result of the query
    Returns wrangled output
    Note that you will often need to define a new SQLModel for validating at this stage
    """
    # TODO: error checking / at the v least check the columns exist
    for col in df.columns:
        assert col in model_cols
    df.replace({"id_in_application": obs_types_inverse}, inplace=True)
    df["value"] = df["value_as_real"]
    df = news_as_int(df)
    df = bp_as_int(df)
    df = air_or_o2_as_int(df)
    df = avpu_as_int(df)
    return df
