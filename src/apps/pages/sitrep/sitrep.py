# src/apps/sitrep/sitrep.py
"""
sub-application for sitrep
"""

from collections import OrderedDict
from typing import List

import dash_bootstrap_components as dbc
import pandas as pd
import requests
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html, register_page

import utils
from api.sitrep.model import SitrepRead
from config.settings import settings
from utils import icons
from utils.beds import get_bed_list, unpack_nested_dict, BedBonesBase
from utils.dash import df_from_store, get_results_response, validate_json
from utils.wards import wards

register_page(__name__)

BPID = "sit_"

DEPT2WARD_MAPPING = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
}


def build_api_url(ward: str = None) -> str:
    """Construct API based on environment and requested ward"""
    if settings.ENV == "prod":
        ward = ward.upper() if ward else "TO3"
        API_URL = f"{settings.BASE_URL}:5006/live/icu/{ward}/ui"
    else:
        API_URL = f"{settings.API_URL}/sitrep/"
    return API_URL


REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds
COLS_ABACUS = [
    "open",
    "unit_order",
    "room",
    "bed",
    "name",
    "mrn",
    "admission_age_years",
    "sex",
    "organ_icons",
    "discharge_ready_1_4h",
]
COLS = OrderedDict(
    {
        "open": "Open",
        "closed": "Closed",
        "unit_order": "Order",
        "ward_code": "Ward",
        "bay_code": "Bay",
        "room": "Bay",
        "bed_code": "Bed code",
        "bed": "Bed",
        "admission_dt": "Admission",
        "elapsed_los_td": "LoS",
        "mrn": "MRN",
        "name": "Full Name",
        "admission_age_years": "Age",
        "sex": "Sex",
        # "dob": "DoB",
        "wim_1": "WIM-P",
        "wim_r": "WIM-R",
        "bed_empty": "Empty",
        "team": "Side",
        "vent_type_1_4h": "Ventilation",
        "n_inotropes_1_4h": "Cardiovascular",
        "had_rrt_1_4h": "Renal",
        "organ_icons": "Organ Support",
        "discharge_ready_1_4h": "Discharge",
        "covid": "COVID",
    }
)


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

    beds = validate_json(beds,BedBonesBase, to_dict=True)

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
    Output(f"{BPID}simple_table", "children"),
    Input(f"{BPID}request_data", "data"),
    # prevent_initial_call=True,
)
def gen_simple_table(data: dict):
    df = df_from_store(data, SitrepRead)
    # limit columns here
    return [
        dt.DataTable(
            id=f"{BPID}simple_table_contents",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            filter_action="native",
            sort_action="native",
        )
    ]


@callback(
    Output(f"{BPID}fancy_table", "children"),
    Input(f"{BPID}request_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    dfo = pd.DataFrame.from_records(data)
    dfo["organ_icons"] = ""
    dfo["unit_order"] = dfo["unit_order"].astype(int)

    llist = []
    for t in dfo.itertuples(index=False):

        cvs = icons.cvs(t.n_inotropes_1_4h)
        rs = icons.rs(t.vent_type_1_4h)
        aki = icons.aki(t.had_rrt_1_4h)

        icon_string = f"{rs}{cvs}{aki}"
        ti = t._replace(organ_icons=icon_string)
        llist.append(ti)
    dfn = pd.DataFrame(llist, columns=dfo.columns)

    # 
    dfn['open'] = dfn['closed'].apply(icons.closed)

    # Prep columns with ids and names
    COL_DICT = [{"name": v, "id": k} for k, v in COLS.items() if k in COLS_ABACUS]
    # TODO: add in a method of sorting based on the order in config

    utils.deep_update(
        utils.get_dict_from_list(COL_DICT, "id", "unit_order"),
        dict(type="numeric"),
    )

    utils.deep_update(
        utils.get_dict_from_list(COL_DICT, "id", "organ_icons"),
        dict(presentation="markdown"),
    )
    utils.deep_update(
        utils.get_dict_from_list(COL_DICT, "id", "discharge_ready_1_4h"),
        dict(editable=True),
    )
    utils.deep_update(
        utils.get_dict_from_list(COL_DICT, "id", "discharge_ready_1_4h"),
        dict(presentation="dropdown"),
    )
    utils.deep_update(
        utils.get_dict_from_list(COL_DICT, "id", "open"),
        dict(presentation="markdown"),
    )

    DISCHARGE_OPTIONS = ["Ready", "No", "Review"]


    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=COL_DICT,
            data=dfn.to_dict("records"),
            editable=False,
            dropdown={
                "discharge_ready_1_4h": {
                    "options": [{"label": i, "value": i} for i in DISCHARGE_OPTIONS],
                    "clearable": False,
                },
            },
            style_as_list_view=True,  # remove col lines
            style_cell={
                # "fontSize": 12,
                "font-family": "sans-serif",
                "padding": "2px",
            },
            style_cell_conditional=[
                {"if": {"column_id": "room"}, "textAlign": "right"},
                {"if": {"column_id": "bed"}, "textAlign": "left"},
                {"if": {"column_id": "mrn"}, "textAlign": "left"},
                {"if": {"column_id": "name"}, "textAlign": "left"},
                {"if": {"column_id": "sex"}, "textAlign": "left"},
                {"if": {"column_id": "organ_icons"}, "textAlign": "left"},
                {"if": {"column_id": "name"}, "fontWeight": "bolder"},
                {"if": {"column_id": "discharge_ready_1_4h"}, "textAlign": "left"},
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
                    "color": "maroon"
                },
            ],
            sort_action="native",
            sort_by=[
                {'column_id': 'unit_order', 'direction': 'asc'},
            ],
            cell_selectable=True,  # possible to click and navigate cells
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
