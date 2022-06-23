# src/apps/electives/electives.py
"""
sub-application for electives
"""


import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, State, callback, register_page
from dash import dash_table as dt
from dash import dcc, html

from typing import List

from api.electives.model import ElectivesRead
from config.settings import settings
from utils.dash import df_from_store, get_results_response

register_page(__name__)
BPID = "ELE_"

API_URL = f"{settings.API_URL}/electives"

# Caboodle data so refresh only needs to happen first thing
REFRESH_INTERVAL = 6 * 60 * 60 * 1000  # milliseconds


@callback(
    Output(f"{BPID}request_data", "data"),
    Input(f"{BPID}query_interval", "n_intervals"),
)
def store_data(n_intervals: int) -> dict:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
    return data  # type: ignore


@callback(
    Output(f"{BPID}filtered_data", "data"),
    Input(f"{BPID}service_picker", "value"),
    State(f"{BPID}request_data", "data"),
    prevent_initial_call=True,
)
def filter_data(val: List[str], data: dict) -> dict:
    """
    Update data based on picker
    """
    if val:
        print(val)
        return [row for row in data if row["PrimaryService"] in val]  # type: ignore
    else:
        return data


@callback(
    Output(f"{BPID}fig_electives", "children"),
    Input(f"{BPID}filtered_data", "modified_timestamp"),
    State(f"{BPID}filtered_data", "data"),
    prevent_initial_call=True,
)
def gen_surgeries_over_time(n_intervals: int, data: dict):
    """
    Plot stacked bar
    """
    df = df_from_store(data, ElectivesRead)
    df = (
        df.groupby("PrimaryService")
        .resample("12H", on="PlannedOperationStartInstant")
        .agg({"PatientKey": "size"})
    )
    df.reset_index(inplace=True)
    print(df)
    fig = px.bar(
        df, x="PlannedOperationStartInstant", y="PatientKey", color="PrimaryService"
    )
    return dcc.Graph(id=f"{BPID}fig", figure=fig)


@callback(
    Output(f"{BPID}table_electives", "children"),
    Input(f"{BPID}filtered_data", "modified_timestamp"),
    State(f"{BPID}filtered_data", "data"),
    prevent_initial_call=True,
)
def gen_table_consults(modified: int, data: dict):

    cols = dict(
        PrimaryMrn="MRN",
        AgeInYears="Age",
        PrimaryService="PrimaryService",
        Priority="Priority",
        ElectiveAdmissionType="ElectiveAdmissionType",
        Status="Status",
        Classification="Classification",
        SurgeryDate="SurgeryDate",
        Name="Name",
    )
    return [
        dt.DataTable(
            id="elective_results_table",
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data,
            filter_action="native",
            sort_action="native",
        )
    ]


@callback(
    Output(f"{BPID}service_picker", "options"),
    Input(f"{BPID}request_data", "data"),
    prevent_initial_call=True,
)
def update_service_dropdown(data: dict):
    df = df_from_store(data, ElectivesRead)
    return df["PrimaryService"].sort_values().unique()


card_fig = dbc.Card(
    [
        dbc.CardHeader(html.H6("Elective Surgery over the next week")),
        dbc.CardBody(
            [
                html.Div(
                    dcc.Dropdown(
                        id=f"{BPID}service_picker",
                        value="",
                        placeholder="Pick a surgical specialty",
                        multi=True,
                    )
                ),
                html.Div([html.P("Updates daily")]),
                html.Div(id=f"{BPID}fig_electives"),
            ]
        ),
    ]
)

card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Elective surgery")),
        dbc.CardBody(
            [
                html.Div(id=f"{BPID}table_electives"),
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
        dcc.Interval(
            id=f"{BPID}query_interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}request_data"),
        dcc.Store(id=f"{BPID}filtered_data"),
    ]
)

layout = html.Div(
    [
        main,
        dash_only,
    ],
)