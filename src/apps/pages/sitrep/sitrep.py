# src/apps/sitrep/sitrep.py
"""
sub-application for sitrep
"""

from collections import OrderedDict

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, State, callback
from dash import dash_table as dt
from dash import dcc, html, register_page

import utils
from api.sitrep.model import SitrepRead
from config.settings import settings
from utils import icons
from utils.beds import BedBonesBase, get_bed_list, unpack_nested_dict, update_bed_row
from utils.dash import df_from_store, get_results_response, validate_json

register_page(__name__)

BPID = "sit_"

DEPT2WARD_MAPPING = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
}

BED_BONES_TABLE_ID = 261


def build_api_url(ward: str = None) -> str:
    """Construct API based on environment and requested ward"""
    if settings.ENV == "prod":
        ward = ward.upper() if ward else "TO3"
        API_URL = f"{settings.BASE_URL}:5006/live/icu/{ward}/ui"
    else:
        API_URL = f"{settings.API_URL}/sitrep/"
    return API_URL


REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds

# COLS_ABACUS = [
#     "sideroom",
#     "unit_order",
#     "open",
#     # "room",
#     # "bed",
#     "name",
#     "mrn",
#     "admission_age_years",
#     "sex",
#     "organ_icons",
#     "DischargeReady",
# ]

# NB: the order of this list determines the order of the table
COLS = [
    {"id": "unit_order", "name": "", "type": "numeric"},
    # {"id": "closed", "name": "Closed"},
    {"id": "sideroom", "name": ""},
    # {"id": "sideroom_suffix", "name": ""},
    # {"id": "ward_code", "name": "Ward"},
    # {"id": "bay_code", "name": "Bay"},
    # {"id": "room", "name": "Bay"},
    # {"id": "bed_code", "name": "Bed code"},
    # {"id": "bed", "name": "Bed"},
    # {"id": "admission_dt", "name": "Admission"},
    # {"id": "elapsed_los_td", "name": "LoS"},
    {"id": "mrn", "name": "MRN"},
    {"id": "name", "name": "Full Name"},
    # {"id": "admission_age_years", "name": "Age"},
    # {"id": "sex", "name": "Sex"},
    {"id": "age_sex", "name": "Age Sex"},
    # {"id": "dob", "name": "DoB"},
    {"id": "wim_1", "name": "WIM-P"},
    {"id": "wim_r", "name": "WIM-R"},
    # {"id": "bed_empty", "name": "Empty"},
    # {"id": "team", "name": "Side"},
    # {"id": "vent_type_1_4h", "name": "Ventilation"},
    # {"id": "n_inotropes_1_4h", "name": "Cardiovascular"},
    # {"id": "had_rrt_1_4h", "name": "Renal"},
    {"id": "organ_icons", "name": "Organ Support", "presentation": "markdown"},
    {
        "id": "DischargeReady",
        "name": "D/C",
        "presentation": "dropdown",
        "editable": True,
    },
    {"id": "open", "name": "", "presentation": "markdown"},
    # {"id": "covid", "name": "COVID"},
]


@callback(
    Output(f"{BPID}request_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}ward_radio", "value"),
)
def store_data(n_intervals: int, dept: str) -> list:
    """
    Read data from API then store as JSON
    """
    # get the sitrep data
    ward = DEPT2WARD_MAPPING[dept]
    API_URL = build_api_url(ward)
    sitrep = get_results_response(API_URL)
    # add department into sitrep results for merge
    for i in sitrep:
        i["department"] = dept

    # get the bed skeleton
    beds = get_bed_list(dept)
    beds = unpack_nested_dict(beds, f2unpack="bed_functional", subkey="value")
    beds = unpack_nested_dict(beds, f2unpack="bed_physical", subkey="value")

    beds = validate_json(beds, BedBonesBase, to_dict=True)

    # merge the two
    df_sitrep = pd.DataFrame.from_records(sitrep)
    df_beds = pd.DataFrame.from_records(beds)
    dfm = pd.merge(
        df_beds,
        df_sitrep,
        how="left",
        left_on=["department", "room", "bed"],
        right_on=["department", "bay_code", "bed_code"],
        indicator=True,
        suffixes=("_bed", "_sitrep"),
    )

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
    Input(f"{BPID}request_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    dfo = pd.DataFrame.from_records(data)
    dfo["organ_icons"] = ""
    dfo["unit_order"] = dfo["unit_order"].astype(int)
    dfo["sideroom"] = np.where(
        dfo["bed_physical"].astype(str).str.contains("sideroom"), "SR", ""
    )
    dfo["sideroom_suffix"] = "|"
    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['admission_age_years']:.0f} {row['sex']}"
        if row["mrn"]
        else "",
        axis=1,
    )
    dfo["name"] = dfo["name"].str.upper()

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
        # dbc.CardBody(
        #     [
        #         dcc.Loading(
        #             id="loading-1",
        #             type="default",
        #             children=html.Div(id=f"{BPID}simple_table"),
        #         )
        #     ]
        # ),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}request_data"),
    ]
)

layout = html.Div(
    [
        dbc.Row(dbc.Col([ward_radio_button])),
        dbc.Row(dbc.Col([sitrep_table])),
        dash_only,
    ]
)
