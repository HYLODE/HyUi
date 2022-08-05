# src/apps/sitrep/sitrep.py
"""
sub-application for sitrep
"""

from collections import OrderedDict

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import requests
from dash import Input, Output, State, callback
from dash import dash_table as dt
from dash import dcc, html, register_page

import utils
from api.sitrep.model import SitrepRead
from api.beds.model import BedsRead
from config.settings import settings
from utils import icons
from utils.beds import BedBonesBase, get_bed_list, unpack_nested_dict, update_bed_row
from utils.dash import df_from_store, get_results_response, validate_json
from apps.pages.sitrep import wng

register_page(__name__)

BPID = "sit_"
BED_BONES_TABLE_ID = 261
COLS = wng.COLS
REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds
DEPT2WARD_MAPPING = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
}

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
    Output(f"{BPID}wrangled_data", "data"),
    Input(f"{BPID}beds_data", "data"),
    Input(f"{BPID}census_data", "data"),
    Input(f"{BPID}sitrep_data", "data"),
)
def wrangle_data_for_table(beds: list, census: list, sitrep: list) -> list:
    """
    Wrangles data from beds, census and sitrep into JSON for table
    """
    # assemble data sources
    df_beds = pd.DataFrame.from_records(beds)
    df_beds = df_beds[wng.beds_keep_cols]

    df_census = pd.DataFrame.from_records(census)
    df_census = df_census[wng.census_keep_cols]
    for col in wng.census_keep_cols:
        if col in ['location_string', 'location_id', 'cvl_discharge', 'occupied', 'ghost']:
            continue
        df_census[col] = np.where(df_census['occupied'], dfm[col], None)


    df_sitrep = pd.DataFrame.from_records(sitrep)
    df_sitrep = df_sitrep[wng.sitrep_keep_cols]

    # merge the three data sources

    df_cb = pd.merge(
        df_beds,
        df_census,
        left_on=["location_string"],
        right_on=["location_string"],
        how="left",
        suffixes=("_bed", "_census"),
    )
    dfm = pd.merge(
        df_cb,
        df_sitrep,
        how="left",
        left_on=["department", "room", "bed"],
        right_on=["department", "bay_code", "bed_code"],
        suffixes=("_bed", "_sitrep"),
        indicator="cbs_merge",
    )
    # replace with None ghost values from sitrep
    for col in wng.sitrep_keep_cols:
        if col in ["department", "room", "bed"]:
            continue
        dfm[col] = np.where(dfm['occupied'], dfm[col], None)

    # prepare field
    dfm['age'] = (pd.Timestamp.now() - dfm['date_of_birth'].apply(pd.to_datetime)) / np.timedelta64(1, 'Y')
    dfm['firstname'] = dfm['firstname'].fillna("")
    dfm['lastname'] = dfm['lastname'].fillna("")
    dfm['sex'] = dfm['sex'].fillna("")
    dfm['name'] = dfm.apply(lambda row: f"{row.firstname.title()} {row.lastname.upper()}", axis=1)
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


@callback(
    Output(f"{BPID}fancy_table", "children"),
    Input(f"{BPID}wrangled_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    dfo = pd.DataFrame.from_records(data)
    dfo["organ_icons"] = ""
    dfo["sideroom"] = np.where(
        dfo["bed_physical"].astype(str).str.contains("sideroom"), "SR", ""
    )
    dfo["sideroom_suffix"] = "|"
    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['age']:.0f} {row['sex']}"
        if row["mrn"]
        else "",
        axis=1,
    )

    # --------------------
    # START: Prepare icons
    llist = []
    for t in dfo.itertuples(index=False):

        cvs = icons.cvs(t.n_inotropes_1_4h)
        rs = icons.rs(t.vent_type_1_4h)
        aki = icons.aki(t.had_rrt_1_4h)

        icon_string = f"{rs}{cvs}{aki}"
        ti = t._replace(organ_icons=icon_string)
        llist.append(ti)
    dfn = pd.DataFrame(llist, columns=dfo.columns)

    dfn["open"] = dfn["closed"].apply(icons.closed)
    # END: Prepare icons
    # --------------------

    # Prep columns with ids and names
    dfn.sort_values(by="unit_order", inplace=True)
    # COL_DICT = [i for i in COLS if i['id'] in COLS_ABACUS]

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=COLS,
            data=dfn.to_dict("records"),
            editable=True,
            # fixed_columns={},
            style_table={"width": "100%", "minWidth": "100%", "maxWidth": "100%"},
            dropdown={
                "DischargeReady": {
                    "options": [
                        {"label": "READY", "value": "ready"},
                        {"label": "Review", "value": "review"},
                        {"label": "No", "value": "No"},
                    ],
                    "clearable": False,
                },
            },
            style_as_list_view=True,  # remove col lines
            style_cell={
                "fontSize": 13,
                "font-family": "monospace",
                "padding": "1px",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "sideroom"},
                    "textAlign": "left",
                    "width": "30px",
                    "whitespace": "normal",
                },
                {"if": {"column_id": "open"}, "textAlign": "left", "width": "20px"},
                {"if": {"column_id": "unit_order"}, "width": "20px"},
                {"if": {"column_id": "room"}, "textAlign": "right"},
                {"if": {"column_id": "bed"}, "textAlign": "left"},
                {
                    "if": {"column_id": "mrn"},
                    "textAlign": "left",
                    "font-family": "monospace",
                },
                {
                    "if": {"column_id": "name"},
                    "textAlign": "left",
                    "font-family": "sans-serif",
                    "fontWeight": "bold",
                    "width": "100px",
                },
                {"if": {"column_id": "sex"}, "textAlign": "left"},
                {"if": {"column_id": "organ_icons"}, "textAlign": "left"},
                {"if": {"column_id": "name"}, "fontWeight": "bolder"},
                {"if": {"column_id": "DischargeReady"}, "textAlign": "left"},
            ],
            style_data={"color": "black", "backgroundColor": "white"},
            # striped rows
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(220, 220, 220)",
                },
                {
                    "if": {
                        "filter_query": "{closed} contains true",
                        # "column_id": "closed"
                    },
                    "color": "maroon",
                },
            ],
            # sort_action="native",
            # sort_by=[
            #     {"column_id": "unit_order", "direction": "asc"},
            # ],
            # cell_selectable=True,  # possible to click and navigate cells
            # row_selectable="single",
            markdown_options={"html": True},
            persistence=True,
            persisted_props=["data"],
        ),
    )

    # wrap in container
    dto = [
        dbc.Container(
            dto,
            className="dbc",
        )
    ]
    return dto


ward_radio_button = html.Div(
    [
        # Need a hidden div for the callback with no output
        html.Div(id="hidden-div", style={"display": "none"}),
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}ward_radio",
                    className="dbc d-grid d-md-flex justify-content-md-end btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active btn-primary",
                    options=[
                        {"label": "T03", "value": "UCH T03 INTENSIVE CARE"},
                        {"label": "T06", "value": "UCH T06 SOUTH PACU"},
                        {"label": "GWB", "value": "GWB L01 CRITICAL CARE"},
                        {"label": "WMS", "value": "WMS W01 CRITICAL CARE"},
                        # {"label": "NHNN", "value": "NHNN"},
                    ],
                    value="UCH T03 INTENSIVE CARE",
                )
            ],
            className="dbc",
        ),
        # html.Div(id="which_icu"),
    ],
    className="radio-group",
)

sitrep_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Sitrep details")),
        dbc.CardBody(id=f"{BPID}fancy_table"),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}beds_data"),
        dcc.Store(id=f"{BPID}census_data"),
        dcc.Store(id=f"{BPID}sitrep_data"),
        dcc.Store(id=f"{BPID}wrangled_data"),
    ]
)

layout = html.Div(
    [
        dbc.Row(dbc.Col([ward_radio_button])),
        dbc.Row(dbc.Col([sitrep_table])),
        dash_only,
    ]
)
