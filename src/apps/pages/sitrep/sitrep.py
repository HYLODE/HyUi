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
from utils.dash import df_from_store, get_results_response
from utils.wards import wards

BPID = "sit_"
register_page(__name__)


def get_bed_list(ward: str = "UCH T03 INTENSIVE CARE") -> list:
    """
    Queries the baserow API for a list of beds

    :returns:   Beds for this ward
    """
    BED_BONES_TABLE_ID = 261
    DEPARTMENT_FIELD_ID = 2041
    FIELDS = ["department","room","bed","unit_order","closed","covid","bed_functional","bed_physical"]

    url = f"{settings.BASEROW_URL}/api/database/rows/table/{BED_BONES_TABLE_ID}/"
    payload = {
        "user_field_names": "true",
        f"filter__field_{DEPARTMENT_FIELD_ID}__equal": ward,
        "include": ",".join(FIELDS),
    }
    response = requests.get(
        url,
        headers={"Authorization": f"Token {settings.BASEROW_READWRITE_TOKEN}"},
        params=payload,
    )
    assert response.status_code == 200
    data = response.json()
    nrows = data["count"]
    assert nrows < 100  # default page size
    res = data['results']
    # extract bed functional characteristics into string
    for row in res:
        bfs = row.get('bed_functional', [])
        funcs = [i.get('value', '') for i in bfs]
        row['bed_functional_str'] = '|'.join(funcs)
        row.pop('bed_functional', None)

    # extract bed physical characteristics into string
    for row in res:
        bfs = row.get('bed_physical', [])
        funcs = [i.get('value', '') for i in bfs]
        row['bed_physical_str'] = '|'.join(funcs)
        row.pop('bed_physical', None)

    if settings.VERBOSE:
        df = pd.DataFrame.from_records(res)
        print(df.head())

    return res

wards = get_bed_list()


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
    Input(f"{BPID}ward_radio", "value"),
)
def store_data(n_intervals: int, ward: str) -> list:
    """
    Read data from API then store as JSON
    """
    API_URL = build_api_url(ward)
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
                        {"label": "T03", "value": "T03"},
                        # {"label": "T06", "value": "T06"},
                        {"label": "GWB", "value": "GWB"},
                        {"label": "WMS", "value": "WMS"},
                        # {"label": "NHNN", "value": "NHNN"},
                    ],
                    value="T03",
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
