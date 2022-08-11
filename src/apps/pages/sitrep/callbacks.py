# src/apps/pages/sitrep/callbacks.py
import warnings

import numpy as np
import pandas as pd
import requests
from dash import Input, Output, State, callback, get_app
from flask_caching import Cache

from api.beds.model import BedsRead
from apps.pages.sitrep import (
    BED_BONES_TABLE_ID,
    BEDS_KEEP_COLS,
    BPID,
    CACHE_TIMEOUT,
    CENSUS_KEEP_COLS,
    DEPT2WARD_MAPPING,
    HYMIND_ICU_DISCHARGE_COLS,
    SITREP_KEEP_COLS,
    wng,
)
from config.settings import settings
from utils.beds import BedBonesBase, get_bed_list, unpack_nested_dict, update_bed_row
from utils.dash import get_results_response, validate_json

app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)


@callback(
    Output(f"{BPID}beds_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
# @cache.memoize(timeout=CACHE_TIMEOUT)
# not caching since this is how we update beds
def store_beds(n_intervals: int, dept: str) -> list:
    """
    Stores data from beds api (i.e. skeleton)
    Confusingly census is in BedsRead which is different to BedBones
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
    Input(f"{BPID}ward_radio", "value"),
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_census(n_intervals: int, dept: str) -> list:
    """
    Stores data from census api (i.e. current beds occupant)
    Confusingly BedsRead refers to census
    """
    payload = {"departments": dept}
    res = requests.get(f"{settings.API_URL}/beds", params=payload)
    census = res.json()
    census = validate_json(census, BedsRead, to_dict=True)
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
    Output(f"{BPID}sitrep_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_sitrep(n_intervals: int, dept: str) -> list:
    """
    Stores data from sitrep api (i.e. organ status)
    """
    # get the sitrep data
    # -------------------
    ward = DEPT2WARD_MAPPING[dept]
    API_URL = wng.build_sitrep_url(ward)
    sitrep = get_results_response(API_URL)
    if all([not bool(i) for i in sitrep]):
        warnings.warn("[WARN] store_sitrep returned an empty list of dictionaries")
        return sitrep
    df = pd.DataFrame.from_records(sitrep)
    # df["department"] = dept
    df = df[SITREP_KEEP_COLS]
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}hymind_icu_discharge_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_hymind_icu_discharge(n_intervals: int, dept: str) -> list:
    """
    Stores data from HyMind ICU discharge predictions
    """
    # get the hymind icu discharge data
    # ---------------------------------
    ward = DEPT2WARD_MAPPING[dept]
    API_URL = wng.build_hymind_icu_discharge_url(ward)
    payload = {"ward": ward}
    predictions = get_results_response(API_URL, params=payload)
    if all([not bool(i) for i in predictions]):
        warnings.warn(
            "[WARN] store_hymind_icu_discharge returned an empty list of dictionaries"
        )
        return predictions
    df = pd.DataFrame.from_records(predictions)
    df = df[HYMIND_ICU_DISCHARGE_COLS]
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}patients_data", "data"),
    Input(f"{BPID}census_data", "data"),
    Input(f"{BPID}sitrep_data", "data"),
    Input(f"{BPID}hymind_icu_discharge_data", "data"),
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_patients(census: list, sitrep: list, hymind: list) -> list:
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

    # try to merge on sitrep data
    df_sitrep = pd.DataFrame.from_records(sitrep)
    if len(df_sitrep) == 0:
        df_sitrep = pd.DataFrame(columns=SITREP_KEEP_COLS)
        warnings.warn("[WARN] NO sitrep data available for store_patients")
    # FIXME: worries me that we're doing type conversion
    # ?switch to using the pydantic models but will need to make Optional more fields
    df_sitrep["csn"] = df_sitrep["csn"].astype(int)
    df = pd.merge(
        df,
        df_sitrep,
        how="left",
        left_on=["encounter"],
        right_on=["csn"],
        indicator="_merge_sitrep",
    )
    if df["_merge_sitrep"].str.match("left_only").all():
        warnings.warn(
            "[WARN] sitrep data available but did NOT MATCH census for store_patients"
        )

    # NB: the attempted merge extends the cols even if there are not matches
    # hence safe to try the merge against episode_slice_id below

    # try to merge on hymind data
    df_hymind = pd.DataFrame.from_records(hymind)
    if len(df_hymind) == 0:
        df_hymind = pd.DataFrame(columns=HYMIND_ICU_DISCHARGE_COLS)
        warnings.warn("[WARN] NO hymind data available for store_patients")
    df = pd.merge(
        df,
        df_hymind,
        how="left",
        on=["episode_slice_id"],
        indicator="_merge_hymind",
    )
    if df["_merge_hymind"].str.match("left_only").all():
        warnings.warn(
            "[WARN] hymind data available but did NOT MATCH sitrep for store_patients"
        )

    if settings.VERBOSE:
        print(df.iloc[0])
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}ward_data", "data"),
    Input(f"{BPID}beds_data", "data"),
    Input(f"{BPID}patients_data", "data"),
)
@cache.memoize(
    timeout=CACHE_TIMEOUT
)  # cache decorator must come between callback and function
def store_ward(beds: list, patients: list) -> list:
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
        cols = CENSUS_KEEP_COLS + SITREP_KEEP_COLS + HYMIND_ICU_DISCHARGE_COLS
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

    # prepare field
    dfm["age"] = (
        pd.Timestamp.now() - dfm["date_of_birth"].apply(pd.to_datetime)
    ) / np.timedelta64(1, "Y")
    dfm["firstname"] = dfm["firstname"].fillna("")
    dfm["lastname"] = dfm["lastname"].fillna("")
    dfm["sex"] = dfm["sex"].fillna("")
    dfm["name"] = dfm.apply(
        lambda row: f"{row.firstname.title()} {row.lastname.upper()}", axis=1
    )
    dfm["unit_order"] = dfm["unit_order"].astype(int, errors="ignore")

    # if settings.VERBOSE:
    #     print(dfm.info())

    data = dfm.to_dict("records")
    return data  # type: ignore


@callback(
    Output("hidden-div", "children"),
    Input(f"{BPID}tbl-census", "data_timestamp"),
    State(f"{BPID}tbl-census", "data_previous"),
    State(f"{BPID}tbl-census", "data"),
    prevent_initial_call=True,
)
def diff_table(time, prev_data, data):

    if data is None or prev_data is None:
        print(prev_data)
        return ""

    diff_rows = [(i, x) for i, x in enumerate(data) if x not in prev_data]

    if diff_rows == []:
        return ""

    discharge_status_updated = []

    for row in diff_rows:
        index = row[0]
        new_row = row[1]

        prev_row = prev_data[index]

        # Get the keys with updated data in the row
        diff_keys = [k for k in new_row if new_row[k] != prev_row[k]]

        if "DischargeReady" in diff_keys:
            discharge_status_updated.append(new_row)

    for x in discharge_status_updated:
        row_id = x["id"]
        row_data = {"DischargeReady": x["DischargeReady"]}

        update_bed_row(BED_BONES_TABLE_ID, row_id, row_data)

    return ""
