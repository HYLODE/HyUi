# src/apps/census/census.py
"""
sub-application for census
"""


import dash_bootstrap_components as dbc
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html, page_registry, register_page

from api.census.model import CensusRead
from config.settings import settings
from utils.dash import df_from_store, get_results_response

register_page(__name__)

# APP to define URL
# maybe run by HyUi API backend or maybe external
# e.g
#
# HyUi API backend ...
# API_URL = f"{settings.API_URL}/census/"
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
    # http://uclvlddpragae07:5006/emap/icu/census/T03/
    API_URL = f"{settings.BASE_URL}:5006/emap/icu/census/{WARD}"
else:
    API_URL = f"{settings.API_URL}/census/"

REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds


@callback(
    Output("census_request_data", "data"),
    Input("census_query-interval", "n_intervals"),
)
def store_data(n_intervals: int) -> list:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
    return data  # type: ignore


@callback(
    Output("census_simple_table", "children"),
    Input("census_request_data", "data"),
    # prevent_initial_call=True,
)
def gen_simple_table(data: dict):
    df = df_from_store(data, CensusRead)
    # limit columns here
    return [
        dt.DataTable(
            id="census_simple_table_contents",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            filter_action="native",
            sort_action="native",
        )
    ]


census_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Census details")),
        dbc.CardBody(
            [
                dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=html.Div(id="census_simple_table"),
                )
            ]
        ),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id="census_query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id="census_request_data"),
    ]
)

layout = html.Div(
    [
        census_table,
        dash_only,
    ]
)
