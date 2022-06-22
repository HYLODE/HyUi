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

simple_table = html.Div()

sitrep_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Sitrep details")),
        dbc.CardBody(
            [
                dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=simple_table,
                )
            ]
        ),
    ]
)

dash_only = html.Div(
    [
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        request_data := dcc.Store(id=f"{BPID}request_data"),
    ]
)

layout = html.Div(
    [
        sitrep_table,
        dash_only,
    ]
)


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
def store_data(n_intervals: int, ward: str) -> list:
    """
    Read data from API then store as JSON
    """
    API_URL = build_api_url(ward)
    data = get_results_response(API_URL)
    return data  # type: ignore


@callback(
    Output(simple_table, "children"),
    Input(request_data, "data"),
    # prevent_initial_call=True,
)
def gen_simple_table(data: dict):
    df = df_from_store(data, SitrepRead)
    # limit columns here
    return [
        dt.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            filter_action="native",
            sort_action="native",
        )
    ]
