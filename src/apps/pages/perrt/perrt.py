# src/apps/perrt/perrt.py
"""
sub-application for perrt
"""


import dash_bootstrap_components as dbc
from dash import Input, Output, callback, register_page
from dash import dash_table as dt
from dash import dcc, html
from pydantic import parse_obj_as

from config.settings import settings
from utils import get_model_from_route
from utils.dash import get_results_response

register_page(__name__)
BPID = "PERRT_"
PerrtRead = get_model_from_route("Perrt", "Read")

API_URL = f"{settings.API_URL}/perrt/"

REFRESH_INTERVAL = 30 * 1000  # milliseconds

card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Ward patients")),
        dbc.CardBody(
            [
                html.Div([html.P("UCLH inpatients and vital signs")]),
                table_perrt := html.Div(),
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
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        request_data := dcc.Store(id=f"{BPID}request_data"),
    ]
)

layout = html.Div(
    [
        main,
        dash_only,
    ],
)


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
def store_data(n_intervals: int) -> dict:
    """
    Read data from API then store as JSON
    """
    data = [dict(parse_obj_as(PerrtRead, i)) for i in get_results_response(API_URL)]
    return data  # type: ignore


@callback(
    Output(table_perrt, "children"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def gen_simple_table(data: dict):

    cols = dict(
        mrn="MRN",
        lastname="Last name",
        firstname="First name",
        date_of_birth="DoB",
        dept_name="Ward/Department",
        bed_hl7="Bed",
        perrt_consult_datetime="PERRT consult",
        news_scale_1_max="NEWS (max)",
        news_scale_1_min="NEWS (min)",
    )
    return [
        dt.DataTable(
            id="results_table",
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data,
            filter_action="native",
            sort_action="native",
        )
    ]
