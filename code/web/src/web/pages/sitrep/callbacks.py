import numpy as np
import pandas as pd
import requests
from dash import Input, Output, State, callback

from models.sitrep import SitrepRow, IndividualDischargePrediction, BedRow

# TODO: Give the SitRep module its own CensusRow model.
from models.census import CensusRow
from web.config import get_settings
from web.convert import to_data_frame
from web.pages.sitrep import (
    BPID,
    DEPT2WARD_MAPPING,
)


def _get_beds(department: str) -> list[BedRow]:
    response = requests.get(
        f"{get_settings().api_url}/sitrep/beds/", params={"department": department}
    )
    return [BedRow.parse_obj(row) for row in response.json()]


def _get_census(department: str) -> list[CensusRow]:
    response = requests.get(
        f"{get_settings().api_url}/sitrep/census/", params={"department": [department]}
    )
    return [CensusRow.parse_obj(row) for row in response.json()]


def _get_sitrep(department: str) -> list[SitrepRow]:
    ward = DEPT2WARD_MAPPING[department]
    response = requests.get(f"{get_settings().api_url}/sitrep/live/{ward}/ui")
    return [SitrepRow.parse_obj(row) for row in response.json()]


def _get_discharge_predictions(department: str) -> list[IndividualDischargePrediction]:
    ward = DEPT2WARD_MAPPING[department]
    response = requests.get(
        f"{get_settings().api_url}/sitrep/predictions/discharge/individual/{ward}/"
    )
    return [IndividualDischargePrediction.parse_obj(row) for row in response.json()]


def _merge_patients(
    census: list[CensusRow],
    sitrep: list[SitrepRow],
    hymind: list[IndividualDischargePrediction],
) -> pd.DataFrame:
    census_df = to_data_frame(census, CensusRow)
    sitrep_df = to_data_frame(sitrep, SitrepRow)
    hymind_df = to_data_frame(hymind, IndividualDischargePrediction)

    merged_df = pd.merge(
        census_df,
        sitrep_df,
        how="left",
        left_on=["encounter"],
        right_on=["csn"],
    )

    return pd.merge(
        merged_df,
        hymind_df,
        how="left",
        on=["episode_slice_id"],
    )


@callback(
    output=Output(f"{BPID}ward_data", "data"),
    inputs=[
        Input(f"{BPID}ward_radio", "value"),
        Input(f"{BPID}closed_beds_switch", "value"),
    ],
    background=True,
)
def store_ward(department: str, closed: bool):
    """
    Merges patients onto beds
    """

    beds = _get_beds(department)
    beds_df = to_data_frame(beds, BedRow)

    census = _get_census(department)
    sitrep = _get_sitrep(department)
    predictions = _get_discharge_predictions(department)
    patients_df = _merge_patients(census, sitrep, predictions)

    merged_df = pd.merge(
        beds_df,
        patients_df,
        how="left",
        # FIXME: location_id has been updated since EMAP upgrade since the
        # bed_skeleton is partially hand built then need a better way of
        # managing this for now merge on string rather than id
        on=["location_string"],
    )

    merged_df["age"] = (
        pd.Timestamp.now() - merged_df["date_of_birth"].apply(pd.to_datetime)
    ) / np.timedelta64(1, "Y")
    merged_df["firstname"] = merged_df["firstname"].fillna("")
    merged_df["lastname"] = merged_df["lastname"].fillna("")
    merged_df["sex"] = merged_df["sex"].fillna("")
    merged_df["name"] = merged_df.apply(
        lambda row: f"{row.lastname.upper()}, {row.firstname.title()}", axis=1
    )
    # merged_df["unit_order"] = merged_df["unit_order"].astype(int, errors="ignore")
    # dfm["epic_bed_request"] = dfm["pm_type"].apply(
    #    lambda x: "Ready to plan" if x == "OUTBOUND" else ""
    # )
    # always return not closed; optionally return closed
    if not closed:
        merged_df = merged_df[~merged_df["closed"]]

    # if settings.VERBOSE:
    #     print(dfm.info())

    return merged_df.to_dict("records")


@callback(
    Output("hidden-div-diff-table", "children"),
    Input(f"{BPID}tbl-census", "data_timestamp"),
    State(f"{BPID}tbl-census", "data_previous"),
    State(f"{BPID}tbl-census", "data"),
    prevent_initial_call=True,
)
def diff_table(time, prev_data, data):

    # TODO: Update the discharge status of the patient on the server.
    # Will need to use encounter ID or similar. Previously the discharge
    # status was attached to the bed as opposed to the patient.

    return ""
