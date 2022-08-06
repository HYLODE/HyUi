# src/apps/pages/sitrep/callbacks.py
import numpy as np
import pandas as pd
import requests
from dash import Input, Output, State, callback

from api.beds.model import BedsRead
from api.sitrep.model import SitrepRead
from apps.pages.sitrep import (
    BED_BONES_TABLE_ID,
    BEDS_KEEP_COLS,
    BPID,
    CENSUS_KEEP_COLS,
    COLS,
    DEPT2WARD_MAPPING,
    HYMIND_ICU_DISCHARGE_COLS,
    REFRESH_INTERVAL,
    SITREP_ENV,
    SITREP_KEEP_COLS,
    widgets,
    wng,
)
from config.settings import settings
from utils.beds import BedBonesBase, get_bed_list, unpack_nested_dict, update_bed_row
from utils.dash import df_from_store, get_results_response, validate_json


@callback(
    Output(f"{BPID}beds_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
def store_beds(n_intervals: int, dept: str) -> list:
    """
    Stores data from beds api (i.e. skeleton)
    Confusingly census is in BedsRead which is different to BedBones
    """
    beds = get_bed_list(dept)
    beds = unpack_nested_dict(beds, f2unpack="bed_functional", subkey="value")
    beds = unpack_nested_dict(beds, f2unpack="bed_physical", subkey="value")
    beds = validate_json(beds, BedBonesBase, to_dict=True)
    return beds


@callback(
    Output(f"{BPID}census_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
def store_census(n_intervals: int, dept: str) -> list:
    """
    Stores data from census api (i.e. current beds occupant)
    Confusingly BedsRead refers to census
    """
    payload = {"departments": dept}
    res = requests.get(f"{settings.API_URL}/beds", params=payload)
    census = res.json()
    census = validate_json(census, BedsRead, to_dict=True)
    return census


@callback(
    Output(f"{BPID}sitrep_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
def store_sitrep(n_intervals: int, dept: str) -> list:
    """
    Stores data from sitrep api (i.e. organ status)
    """
    # get the sitrep data
    # -------------------
    ward = DEPT2WARD_MAPPING[dept]
    API_URL = wng.build_sitrep_url(ward)
    sitrep = get_results_response(API_URL)
    # add department into sitrep results for merge
    for i in sitrep:
        i["department"] = dept
    return sitrep


@callback(
    Output(f"{BPID}hymind_icu_discharge_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
def store_hymind_icu_discharge(n_intervals: int, dept: str) -> list:
    """
    Stores data from HyMind ICU discharge predictions
    """
    # get the hymind icu discharge data
    # ---------------------------------
    ward = DEPT2WARD_MAPPING[dept]
    API_URL = wng.build_hymind_icu_discharge_url(ward)
    payload = {"ward": ward}
    data = get_results_response(API_URL, payload=payload)
    return data


@callback(
    Output(f"{BPID}wrangled_data", "data"),
    Input(f"{BPID}beds_data", "data"),
    Input(f"{BPID}census_data", "data"),
    Input(f"{BPID}sitrep_data", "data"),
    Input(f"{BPID}hymind_icu_discharge_data", "data"),
)
def stores_2_table_store(beds: list, census: list, sitrep: list, hymind: list) -> list:
    """
    Wrangles data from beds, census and sitrep into JSON for table
    """
    # assemble data sources
    # BEDS SKELETON
    # -------------
    df_beds = pd.DataFrame.from_records(beds)
    df_beds = df_beds[BEDS_KEEP_COLS]

    # BED CENSUS (via my query)
    # -------------------------
    df_census = pd.DataFrame.from_records(census)
    df_census = df_census[CENSUS_KEEP_COLS]
    for col in CENSUS_KEEP_COLS:
        if col in [
            "location_string",
            "location_id",
            "cvl_discharge",
            "occupied",
            "ovl_ghost",
        ]:
            continue
        df_census[col] = np.where(df_census["occupied"], df_census[col], None)

    # SITREP FEATURES esp. for episode slice id
    # -----------------------------------------
    df_sitrep = pd.DataFrame.from_records(sitrep)
    df_sitrep = df_sitrep[SITREP_KEEP_COLS]

    # HyMIND FEATURES (predictions)
    # -----------------------------------------
    df_hymind = pd.DataFrame.from_records(hymind)
    # import ipdb; ipdb.set_trace()
    df_hymind = df_hymind[HYMIND_ICU_DISCHARGE_COLS]

    # merge the four data sources

    # merge 1
    df_bc = pd.merge(
        df_beds,
        df_census,
        left_on=["location_string"],
        right_on=["location_string"],
        how="left",
        suffixes=("_bed", "_census"),
    )
    # merge 2
    df_bcs = pd.merge(
        df_bc,
        df_sitrep,
        how="left",
        left_on=["department", "room", "bed"],
        right_on=["department", "bay_code", "bed_code"],
        suffixes=("_bed", "_sitrep"),
        indicator="cbs_merge",
    )
    # merge 3
    dfm = pd.merge(
        df_bcs,
        df_hymind,
        how="left",
        left_on=["episode_slice_id"],
        right_on=["episode_slice_id"],
    )
    # replace with None ghost values from sitrep and hymind
    for col in (SITREP_KEEP_COLS + list(df_hymind.columns)):
        if col in ["department", "room", "bed"]:
            continue
        dfm[col] = np.where(dfm["occupied"], dfm[col], None)

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
    dfm["unit_order"] = dfm["unit_order"].astype(int)

    if settings.VERBOSE:
        print(dfm.info())

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
