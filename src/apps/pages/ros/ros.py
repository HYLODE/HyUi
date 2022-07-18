# src/apps/electives/electives.py
"""
sub-application for electives
"""


import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, State, callback, register_page
from dash import dash_table as dt
from dash import dcc, html

from config.settings import settings
from utils.dash import get_results_response

from datetime import datetime

import pandas as pd


register_page(__name__)
BPID = "ROS_"

API_URL = f"{settings.API_URL}/ros"

# Caboodle data so refresh only needs to happen first thing
REFRESH_INTERVAL = 6 * 60 * 60 * 1000  # milliseconds

card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("ROS status of patients")),
        dbc.CardBody(
            [
                patient_table := html.Div(),
            ]
        ),
    ]
)

main = html.Div(
    [
        card_table,
        # pie_chart := dcc.Graph(),
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
    data = get_results_response(API_URL)

    for row in data:
        admission_time = datetime.fromisoformat(row["admission_time"])
        row["admission_time_str"] = admission_time.strftime("%d-%m-%y %H:%M")

        row["ros_status"] = "To do"

        if row["order_datetime"] is not None:
            order_datetime = datetime.fromisoformat(row["order_datetime"])

            row["order_datetime_str"] = order_datetime.strftime("%d-%m-%y %H:%M")
            last_ros_date = order_datetime.date()

            row["ros_status"] = (
                "Complete" if last_ros_date >= admission_time.date() else "To do"
            )

            row["ros_status"] = (
                "Waiting results.." if row["lab_result_id"] is None else "Complete"
            )

    	data = sorted(data, key=lambda d: d['bed_name'])

    return data  # type: ignore


@callback(
    Output("pie_chart", "figure"),
    Input(request_data, "modified_timestamp"),
    State(request_data, "data"),
    prevent_initial_call=True,
)
def gen_pie_chart(modified: int, data):
    df = pd.DataFrame(data)

    fig = px.pie(df, values="id", names=["Tested", "Ordered", "Not ordered"])

    return fig


@callback(
    Output(patient_table, "children"),
    Input(request_data, "modified_timestamp"),
    State(request_data, "data"),
    prevent_initial_call=True,
)
def gen_patient_table(modified: int, data: dict):

    cols = dict(
        bed_name="Bed name",
        live_mrn="MRN",
        date_of_birth="Date of birth",
        firstname="First name",
        lastname="Last name",
        admission_time_str="Admission time",
        order_datetime_str="Last order",
        lab_result_id="Lab result ID",
        ros_status="ROS status",
    )

    return [
        dt.DataTable(
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data,
            sort_action="native",
            style_cell={
                # "fontSize": 12,
                "font-family": "sans-serif",
                "padding": "2px",
            },
            editable=False,
            style_data_conditional=[
                {
                    "if": {
                        "column_id": "ros_status",
                        "filter_query": "{ros_status} = 'To do'",
                    },
                    "backgroundColor": "tomato",
                    "color": "white",
                },
                {
                    "if": {
                        "column_id": "ros_status",
                        "filter_query": "{ros_status} = Complete or "
                        " {ros_status} = 'Waiting results..'",
                    },
                    "backgroundColor": "green",
                    "color": "white",
                },
            ],
        )
    ]
