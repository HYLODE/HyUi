# src/apps/consults/consults.py
"""
sub-application for consults
"""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html

from api.sitrep.model import SitrepRead

# from config.settings import settings
from utils.dash import df_from_store, get_results_response

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


WARD = "T03"  # initial definition
API_URL = f"http://172.16.149.205:5006/icu/live/{WARD}/ui"

REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds


@callback(
    Output("request_data", "data"),
    Input("query-interval", "n_intervals"),
)
def store_data(n_intervals: int) -> list:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
    data = data["data"]
    return data  # type: ignore


@callback(
    Output("simple_table", "children"),
    Input("request_data", "data"),
    prevent_initial_call=True,
)
def gen_simple_table(data: dict):
    df = df_from_store(data, SitrepRead)
    return [
        dt.DataTable(
            id="simple_table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=data,
            filter_action="native",
            sort_action="native",
        )
    ]


card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Sitrep details")),
        dbc.CardBody(
            [
                html.Div(id="simple_table"),
            ]
        ),
    ]
)

main = html.Div(
    [
        card_table,
    ]
)


dash_only = html.Div(
    [
        dcc.Interval(id="query-interval", interval=REFRESH_INTERVAL, n_intervals=0),
        dcc.Store(id="request_data"),
    ]
)

sitrep = dbc.Container(
    fluid=True,
    className="dbc",
    children=[
        main,
        dash_only,
    ],
)
