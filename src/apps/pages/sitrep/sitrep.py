# src/apps/consults/consults.py
"""
sub-application for consults
"""

import pandas as pd
from collections import OrderedDict

import dash_bootstrap_components as dbc
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html
from dash import register_page

from api.sitrep.model import SitrepRead

from config.settings import settings
import utils
from utils.dash import df_from_store, get_results_response
from utils import icons

BPID = "sit_"
register_page(__name__)

# APP to define URL
# maybe run by HyUi API backend or maybe external
# e.g
#
# HyUi API backend ...
# API_URL = f"{settings.API_URL}/consults/"
#
# External (HySys) backend ..
# then define locally here within *this* app
# API_URL = http://172.16.149.205:5006/icu/live/{ward}/ui
#
# External (gov.uk) backend ...
# API_URL = f"https://coronavirus.data.gov.uk/api/v2/data ..."
#
# the latter two are defined as constants here

if settings.ENV == "prod":
    WARD = "T03"  # initial definition
    API_URL = f"{settings.BASE_URL}:5006/live/icu/{WARD}/ui"
else:
    API_URL = f"{settings.API_URL}/sitrep/"

REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds
COLS_ABACUS = [
    "bay_code",
    "bed_code",
    "name",
    "mrn",
    "admission_age_years",
    "sex",
    "organ_icons",
    "discharge_ready_1_4h",
]
COLS = OrderedDict(
    {
        "ward_code": "Ward",
        "bay_code": "Bay",
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
    }
)


@callback(
    Output(f"{BPID}request_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
)
def store_data(n_intervals: int) -> list:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
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

    llist = []
    for t in dfo.itertuples(index=False):

        cvs = icons.cvs(t.n_inotropes_1_4h)
        rs = icons.rs(t.vent_type_1_4h)
        aki = icons.aki(t.had_rrt_1_4h)

        icon_string = f"{rs}{cvs}{aki}"
        ti = t._replace(organ_icons=icon_string)
        llist.append(ti)
    dfn = pd.DataFrame(llist, columns=dfo.columns)

    # Prep columns with ids and names
    COL_DICT = [{"name": v, "id": k} for k, v in COLS.items() if k in COLS_ABACUS]
    # TODO: add in a method of sorting based on the order in config

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
                {"if": {"column_id": "bay_code"}, "textAlign": "right"},
                {"if": {"column_id": "bed_code"}, "textAlign": "left"},
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
                }
            ],
            sort_action="native",
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
        sitrep_table,
        dash_only,
    ]
)
