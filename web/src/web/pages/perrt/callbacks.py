import warnings

import numpy as np
import pandas as pd
import requests
from dash import Input, Output, callback, dcc, get_app
from flask_caching import Cache

from models.census import CensusRow, CensusBed
from web.config import get_settings
from web.census import fetch_department_census
from web.convert import to_data_frame
from web.hospital import get_building_departments
from web.pages.perrt import (
    BEDS_KEEP_COLS,
    BPID,
)

CENSUS_KEEP_COLS = [
    "location_string",
    "location_id",
    "ovl_admission",
    "ovl_hv_id",
    "cvl_discharge",
    "occupied",
    "ovl_ghost",
    "mrn",
    "encounter",
    "date_of_birth",
    "lastname",
    "firstname",
    "sex",
    "planned_move",
    "pm_datetime",
    "pm_type",
    "pm_dept",
    "pm_location_string",
]


def _unpack_nested_dict(
    rows: list[dict],
    f2unpack: str,
    subkey: str,
    new_name: str = "",
) -> list[dict]:
    """
    Unpack fields with nested dictionaries

    :param      rows:  The rows
    :param      f2unpack:  field to unpack
    :param      subkey:  key within nested dictionary to use
    :param      new_name: new name for field else overwrite if None

    :returns:   { description_of_the_return_value }
    """
    for row in rows:
        i2unpack = row.get(f2unpack, [])
        vals = [i.get(subkey, "") for i in i2unpack]
        vals_str = "|".join(vals)
        if new_name:
            row[new_name] = vals_str
        else:
            row.pop(f2unpack, None)
            row[f2unpack] = vals_str
    return rows


@callback(
    Output(f"{BPID}dept_dropdown_div", "children"),
    Input(f"{BPID}building_radio", "value"),
)
def gen_dept_dropdown(building: str):
    """
    Dynamically build department picker list

    :param      building:  The building
    :type       building:  str

    :returns:   { description_of_the_return_value }
    :rtype:     list
    """

    building_departments = get_building_departments()
    departments: list[str] = []
    for bd in building_departments:
        if bd.building == building:
            departments.extend(bd.departments)
            break

    default_value = departments[0]
    return dcc.Dropdown(
        id=f"{BPID}dept_dropdown",
        value=default_value,
        options=[{"label": v, "value": v} for v in departments],
        placeholder="Pick a department",
        # NOTE: converting this to multi would require changing all the
        #  endpoints to handle a list of strings (i.e. list of depts)
        multi=False,
    )


def _get_bed_list(department: str) -> list[CensusBed]:
    """Returns bed not patient level data from BaseRow for that department"""
    response = requests.get(
        f"{get_settings().api_url}/census/beds/", params={"department": department}
    )
    return [CensusBed.parse_obj(row) for row in response.json()]


@callback(
    Output(f"{BPID}dept_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}building_radio", "value"),
)
def store_depts(*args, **kwargs):
    return fetch_department_census()


@callback(
    Output(f"{BPID}beds_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_call=True,
)
def store_beds(n_intervals: int, dept: str):
    """
    Stores data from census api (i.e. skeleton)
    """
    beds = [i.dict() for i in _get_bed_list(dept)]
    beds = _unpack_nested_dict(beds, f2unpack="bed_functional", subkey="value")
    beds = _unpack_nested_dict(beds, f2unpack="bed_physical", subkey="value")

    if all([not bool(i) for i in beds]):
        warnings.warn("[WARN] store_beds returned an empty list of dictionaries")
        return beds
    df = pd.DataFrame.from_records(beds)
    df = df[BEDS_KEEP_COLS]
    mask = df["bed_physical"].str.contains("virtual")
    df = df[~mask]
    return df.to_dict(orient="records")


def _get_census(departments: list[str]) -> list[CensusRow]:
    """returns current department census"""
    response = requests.get(
        f"{get_settings().api_url}/census/", params={"departments": departments}
    )
    return [CensusRow.parse_obj(row) for row in response.json()]


@callback(
    Output(f"{BPID}census_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_call=True,
)
def store_census(n_intervals: int, departments: list[str]):
    """
    Stores data from census api (i.e. current beds occupant)
    """

    census = _get_census(departments)
    census_df = to_data_frame(census, CensusRow)

    census_df = census_df[CENSUS_KEEP_COLS]

    # Scrub ghosts with the occupied mask.
    return census_df[census_df["occupied"]].to_dict(orient="records")


@callback(
    Output(f"{BPID}patients_data", "data"),
    Input(f"{BPID}census_data", "data"),
    prevent_initial_call=True,
)
def store_patients(census: list):
    """
    Assembles patient level info (without beds)

    :returns:   { description_of_the_return_value }
    :rtype:     list
    """
    # Load data into dataframes; ensure columns exist even if store is empty

    df_census = pd.DataFrame.from_records(census)
    if len(df_census) == 0:
        warnings.warn("[WARN] store_patients returned an empty list of dictionaries")
        return [{}]
    else:
        df = df_census.copy()

    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}ward_data", "data"),
    Input(f"{BPID}beds_data", "data"),
    Input(f"{BPID}patients_data", "data"),
    Input(f"{BPID}closed_beds_switch", "value"),
    prevent_initial_call=True,
)
def store_ward(beds: list, patients: list, closed: bool) -> list:
    """
    Merges patients onto beds
    """
    if not beds:
        warnings.warn("[WARN] store_beds returned an empty list of dictionaries")
        return []
    df_beds = pd.DataFrame.from_records(beds)

    if patients:
        df_pats = pd.DataFrame.from_records(patients)
    else:
        warnings.warn("[WARN] NO patients found for these beds")
        # prepare empty dataframe so the remainder of the function can run
        cols = CENSUS_KEEP_COLS
        df_pats = pd.DataFrame(columns=cols)

    dfm = pd.merge(
        df_beds,
        df_pats,
        how="left",
        # FIXME: location_id has been updated since EMAP upgrade since the
        # bed_skeleton is partially hand built then need a better way of
        # managing this for now merge on string rather than id
        on=["location_string"],
        # on=["location_id"],
        indicator="_merge_ward",
    )

    # prepare fields
    dfm["age"] = (
        pd.Timestamp.now() - dfm["date_of_birth"].apply(pd.to_datetime)
    ) / np.timedelta64(1, "Y")
    dfm["firstname"] = dfm["firstname"].fillna("")
    dfm["lastname"] = dfm["lastname"].fillna("")
    dfm["sex"] = dfm["sex"].fillna("")
    dfm["name"] = dfm.apply(
        lambda row: f"{row.lastname.upper()}, {row.firstname.title()}", axis=1
    )

    # always return not closed; optionally return closed
    if not closed:
        dfm = dfm[~dfm["closed"]]

    data = dfm.to_dict("records")
    return data  # type: ignore
