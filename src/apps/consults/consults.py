# src/apps/consults/consults.py
"""
sub-application for consults
"""

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, State, callback
from dash import dash_table as dt
from dash import dcc, html

from api.consults.model import ConsultsRead
from config.settings import settings
from utils.dash import df_from_store, get_results_response

REFRESH_INTERVAL = 5 * 60 * 1000  # milliseconds
API_URL = f"{settings.BACKEND_URL}/consults/"


@callback(
    Output("request_data", "data"),
    Input("query-interval", "n_intervals"),
)
def store_data(n_intervals: int) -> dict:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
    return data  # type: ignore


@callback(
    Output("filtered_data", "data"),
    Input("department_picker", "value"),
    State("request_data", "data"),
)
def filter_data(val: str, data: dict) -> dict:
    """
    Update data based on picker
    """
    if val:
        print(val)
        return [row for row in data if row["dept_name"] == val]  # type: ignore
    else:
        return data


@callback(
    Output("fig_consults", "children"),
    Input("filtered_data", "modified_timestamp"),
    State("filtered_data", "data"),
    # prevent_initial_call=True,
)
def gen_consults_over_time(n_intervals: int, data: dict):
    """
    Plot stacked bar
    """
    df = df_from_store(data, ConsultsRead)
    df = (
        df.groupby("name")
        .resample("6H", on="scheduled_datetime")
        .agg({"dept_name": "size"})
    )
    df.reset_index(inplace=True)
    fig = px.bar(df, x="scheduled_datetime", y="dept_name", color="name")
    return dcc.Graph(id="consults_fig", figure=fig)


@callback(
    Output("table_consults", "children"),
    Input("filtered_data", "modified_timestamp"),
    State("filtered_data", "data"),
    prevent_initial_call=True,
)
def gen_table_consults(modified: int, data: dict):

    cols = dict(
        dept_name="Ward/Department",
        firstname="First name",
        lastname="Last name",
        date_of_birth="DoB",
        mrn="MRN",
        name="Consult",
        scheduled_datetime="Consult time",
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


@callback(
    Output("department_picker", "options"),
    Input("request_data", "data"),
)
def update_dept_dropdown(data: dict) -> list:
    df = df_from_store(data, ConsultsRead)
    return sorted(df["dept_name"].unique())


card_fig = dbc.Card(
    [
        dbc.CardHeader(html.H6("Real time consults over the last 72")),
        dbc.CardBody(
            [
                html.Div(
                    dcc.Dropdown(
                        id="department_picker",
                    )
                ),
                html.Div([html.P("Updates every 5 mins")]),
                html.Div(id="fig_consults"),
            ]
        ),
    ]
)

card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Consult details")),
        dbc.CardBody(
            [
                html.Div([html.P("Consults launched from ED")]),
                html.Div(id="table_consults"),
            ]
        ),
    ]
)

main = html.Div(
    [
        card_fig,
        card_table,
    ]
)


dash_only = html.Div(
    [
        dcc.Interval(id="query-interval", interval=REFRESH_INTERVAL, n_intervals=0),
        dcc.Store(id="request_data"),
        dcc.Store(id="filtered_data"),
    ]
)

consults = dbc.Container(
    fluid=True,
    className="dbc",
    children=[
        main,
        dash_only,
    ],
)
