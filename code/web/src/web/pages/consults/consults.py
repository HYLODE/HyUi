"""
sub-application for consults
"""
from typing import Any, cast

import dash_bootstrap_components as dbc
import plotly.express as px
import requests
from dash import Input, Output, State, callback, register_page
from dash import dash_table as dt
from dash import dcc, html
from flask_login import current_user

from models.consults import Consults

from web.config import get_settings
from web.convert import parse_to_data_frame

register_page(__name__)
BPID = "CON_"


REFRESH_INTERVAL = 5 * 60 * 1000  # milliseconds

card_fig = dbc.Card(
    [
        dbc.CardHeader(html.H6("Real time consults over the last 72")),
        dbc.CardBody(
            [
                html.Div(
                    department_picker := dcc.Dropdown(
                        value="",
                        placeholder="Pick a consult type",
                    )
                ),
                html.Div([html.P("Updates every 5 mins")]),
                fig_consults := html.Div(),
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
                table_consults := html.Div(),
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
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        request_data := dcc.Store(id=f"{BPID}request_data"),
        filtered_data := dcc.Store(id=f"{BPID}filtered_data"),
    ]
)


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])
    return html.Div(
        [
            main,
            dash_only,
        ],
    )


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
def store_data(n_intervals: int) -> dict[str, Any]:
    """
    Read data from API then store as JSON
    """
    response = requests.get(f"{get_settings().api_url}/consults/")
    return cast(dict[str, Any], response.json())


# TODO: This function and its types are probably wrong.
@callback(
    Output(filtered_data, "data"),
    Input(department_picker, "value"),
    State(request_data, "data"),
    prevent_initial_call=True,
)
def filter_data(val: str | None, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Update data based on picker
    """
    if val:
        return [row for row in data if row["dept_name"] == val]
    else:
        return data


@callback(
    Output(fig_consults, "children"),
    Input(filtered_data, "modified_timestamp"),
    State(filtered_data, "data"),
    prevent_initial_call=True,
)
def gen_consults_over_time(n_intervals: int, data: list[dict]):
    """
    Plot stacked bar
    """
    df = parse_to_data_frame(data, Consults)
    df = (
        df.groupby("name")
        .resample("6H", on="scheduled_datetime")
        .agg({"dept_name": "size"})
    )
    df.reset_index(inplace=True)
    fig = px.bar(df, x="scheduled_datetime", y="dept_name", color="name")
    return dcc.Graph(id="consults_fig", figure=fig)


@callback(
    Output(table_consults, "children"),
    Input(filtered_data, "modified_timestamp"),
    State(filtered_data, "data"),
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
    Output(department_picker, "options"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def update_dept_dropdown(data: list[dict]):
    # df = df_from_store(data, ConsultsRead)
    df = parse_to_data_frame(data, Consults)
    return df["dept_name"].sort_values().unique()
