# src/apps/pages/census/callbacks.py
import importlib
import warnings

import numpy as np
import pandas as pd
import requests
from dash import Input, Output, callback, dcc, get_app
from flask_caching import Cache

from api.census.model import CensusDepartments, CensusRead
from apps.pages.census import (
    BEDS_KEEP_COLS,
    BPID,
    CACHE_TIMEOUT,
    CENSUS_API_URL,
    CENSUS_KEEP_COLS,
    DEPARTMENTS_API_URL,
    DEPT_KEEP_COLS,
)
from config.settings import settings
from utils.beds import (
    BedBonesBase,
    get_bed_list,
    get_closed_beds,
    unpack_nested_dict,
)
from utils.dash import validate_json

# this structure is necessary for flask_cache
app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)


@callback(
    Output(f"{BPID}dept_dropdown_div", "children"),
    Input(f"{BPID}building_radio", "value"),
)
def gen_dept_dropdown(building: str) -> list:
    """
    Dynamically build department picker list

    :param      building:  The building
    :type       building:  str

    :returns:   { description_of_the_return_value }
    :rtype:     list
    """
    dept_list = getattr(importlib.import_module("utils.wards"), building)
    default_value = dept_list[0]
    return dcc.Dropdown(
        id=f"{BPID}dept_dropdown",
        value=default_value,
        options=[{"label": v, "value": v} for v in dept_list],
        placeholder="Pick a department",
        multi=False,
    )


def store_depts_fn(n_intervals: int, building: str) -> list:
    """
    Stores data from census api (i.e. skeleton)
    Also reaches out to bed_bones and pulls in additional closed beds
    """
    res = requests.get(DEPARTMENTS_API_URL)
    depts = res.json()
    depts = validate_json(depts, CensusDepartments, to_dict=True)
    if all([not bool(i) for i in depts]):
        warnings.warn("[WARN] store_census returned an empty list of dictionaries")
        return depts
    df = pd.DataFrame.from_records(depts)
    if building:
        dept_list = getattr(importlib.import_module("utils.wards"), building)
        df = df[df["department"].isin(dept_list)]

    # Now update with closed beds from bed_bones
    df_closed = pd.DataFrame.from_records(get_closed_beds())
    closed = df_closed.groupby("department")["closed"].sum()
    df = df.merge(closed, on="department", how="left")
    df["closed"].fillna(0, inplace=True)

    # Then update empties
    df["empties"] = df["empties"] - df["closed"]

    df = df[DEPT_KEEP_COLS]
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}dept_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}building_radio", "value"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_depts(*args, **kwargs):
    return store_depts_fn(*args, **kwargs)


@callback(
    Output(f"{BPID}beds_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_call=True,
)
# @cache.memoize(timeout=CACHE_TIMEOUT)
# not caching since this is how we update beds
def store_beds(n_intervals: int, dept: str) -> list:
    """
    Stores data from census api (i.e. skeleton)
    """
    beds = get_bed_list(dept)
    beds = unpack_nested_dict(beds, f2unpack="bed_functional", subkey="value")
    beds = unpack_nested_dict(beds, f2unpack="bed_physical", subkey="value")
    beds = validate_json(beds, BedBonesBase, to_dict=True)
    if all([not bool(i) for i in beds]):
        warnings.warn("[WARN] store_beds returned an empty list of dictionaries")
        return beds
    df = pd.DataFrame.from_records(beds)
    df = df[BEDS_KEEP_COLS]
    mask = df["bed_physical"].str.contains("virtual")
    df = df[~mask]
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}census_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_call=True,
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_census(n_intervals: int, dept: str) -> list:
    """
    Stores data from census api (i.e. current beds occupant)
    """
    payload = {"departments": dept}
    res = requests.get(CENSUS_API_URL, params=payload)
    census = res.json()
    census = validate_json(census, CensusRead, to_dict=True)
    if all([not bool(i) for i in census]):
        warnings.warn("[WARN] store_census returned an empty list of dictionaries")
        return census
    df = pd.DataFrame.from_records(census)
    df = df[CENSUS_KEEP_COLS]
    # scrub ghosts
    mask = df["occupied"]
    df = df[mask]
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}patients_data", "data"),
    Input(f"{BPID}census_data", "data"),
    prevent_initial_call=True,
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_patients(census: list) -> list:
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

    if settings.VERBOSE:
        print(df.iloc[0])
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}ward_data", "data"),
    Input(f"{BPID}beds_data", "data"),
    Input(f"{BPID}patients_data", "data"),
    Input(f"{BPID}closed_beds_switch", "value"),
    prevent_initial_call=True,
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_ward(beds: list, patients: list, closed: bool) -> list:
    """
    Merges patients onto beds
    """
    df_beds = pd.DataFrame.from_records(beds)
    if len(df_beds) == 0:
        warnings.warn("[WARN] store_beds returned an empty list of dictionaries")
        return [{}]

    df_pats = pd.DataFrame.from_records(patients)
    if len(df_pats) == 0:
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
    # dfm["unit_order"] = dfm["unit_order"].astype(int, errors="ignore")
    # dfm["epic_bed_request"] = dfm["pm_type"].apply(lambda x: "Ready to plan" if x == "OUTBOUND" else "")
    # always return not closed; optionally return closed
    if not closed:
        dfm = dfm[dfm["closed"] == False]

    # if settings.VERBOSE:
    #     print(dfm.info())

    data = dfm.to_dict("records")
    return data  # type: ignore
