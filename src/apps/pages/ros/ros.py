# src/apps/ros/ros.py
"""
sub-application for ros
"""


import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, State, callback, register_page
from dash import dash_table as dt
from dash import dcc, html

from config.settings import settings
from utils.dash import get_results_response

from datetime import datetime, date, timedelta

import pandas as pd
import numpy as np

register_page(__name__, name="ROS")
BPID = "ROS_"

API_URL = f"{settings.API_URL}/ros"

# Caboodle data so refresh only needs to happen first thing
REFRESH_INTERVAL = 6 * 60 * 60 * 1000  # milliseconds

ward_radio_button = html.Div(
    [
        html.Div(
            [
                ward_radio := dbc.RadioItems(
                    className="dbc d-grid d-md-flex justify-content-md-end btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active btn-primary",
                    options=[
                        {"label": "T03", "value": "UCH T03 INTENSIVE CARE"},
                        {"label": "GWB", "value": "GWB L01 CRITICAL CARE"},
                        {"label": "WMS", "value": "WMS W01 CRITICAL CARE"},
                    ],
                    value="UCH T03 INTENSIVE CARE",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)


card_table = dbc.Card(
    [
        dbc.CardHeader(html.H5("Infection control screening dashboard")),
        dbc.CardBody(
            [
                patient_table := html.Div(),
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
        ward_radio_button,
        card_table,
        # pie_chart := dcc.Graph(),
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

    pts_by_department = dict()  # stores the patient lists keyed on the department name

    for row in data:
        # Format admission date for table
        admission_time = datetime.fromisoformat(row["hospital_admission_datetime"])
        row["admission_time_str"] = admission_time.strftime("%d-%m-%y %H:%M")

        # Prepare ROS data
        row["ros_order_status"] = "To do"

        if row["ros_order_datetime"] is not None:
            order_datetime = datetime.fromisoformat(row["ros_order_datetime"])
            row["ros_order_datetime_str"] = order_datetime.strftime("%d-%m-%y %H:%M")
            last_ros_date = order_datetime.date()

            if (
                last_ros_date >= admission_time.date()
            ):  # If a test has been ordered during this admission
                if (
                    row["ros_lab_result_id"] is not None
                ):  # And there is a result back: screening complete
                    row["ros_order_status"] = "Complete"
                else:  # If there is no result, we are awaiting results
                    row["ros_order_status"] = "Awaiting results"

        # Prepare MRSA data
        row["mrsa_order_status"] = "To do"

        if row["mrsa_order_datetime"] is not None:
            order_datetime = datetime.fromisoformat(row["mrsa_order_datetime"])
            row["mrsa_order_datetime_str"] = order_datetime.strftime("%d-%m-%y %H:%M")
            last_mrsa_date = order_datetime.date()

            if last_mrsa_date >= (
                date.today() - timedelta(7)
            ):  # If MRSA screening done in last 7 days
                if (
                    row["mrsa_lab_result_id"] is not None
                ):  # And we have a result, then we are finished
                    row["mrsa_order_status"] = "Complete"
                else:  # Else we are awaiting results
                    row["mrsa_order_status"] = "Awaiting results"

        # Add data to the individual department list
        dept_list = pts_by_department.get(row["department"], [])
        dept_list.append(row)
        dept_list = sorted(dept_list, key=lambda d: d["bed_name"])
        pts_by_department[row["department"]] = dept_list

    return pts_by_department


# @callback(
#     Output(pie_chart, "figure"),
#     Input(request_data, "modified_timestamp"),
#     Input(ward_radio, "value"),
#     State(request_data, "data"),
#     prevent_initial_call=True,
# )
# def gen_pie_chart(modified: int, ward: str, data: dict):
#     df = pd.DataFrame(data[ward])
#     df["is_complete"] = df["mrsa_order_status"].ne("To do").mul(1)
#     df["names"] = np.where(df["is_complete"]==1, 'Complete', 'Not done')

#     fig = px.pie(df, values="mrsa_order_status", names="names")

#     return fig


@callback(
    Output(patient_table, "children"),
    Input(request_data, "modified_timestamp"),
    Input(ward_radio, "value"),
    State(request_data, "data"),
    prevent_initial_call=True,
)
def gen_patient_table(modified: int, ward: str, data: dict):

    cols = dict(
        bed_name="Bed name",
        mrn="MRN",
        date_of_birth="Date of birth",
        firstname="First name",
        lastname="Last name",
        admission_time_str="Admission time",
        ros_order_datetime_str="Last ROS order",
        ros_order_status="ROS order status",
        mrsa_order_datetime_str="Last MRSA order",
        mrsa_order_status="MRSA order status",
    )

    return [
        dt.DataTable(
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data.get(ward, []),
            sort_action="native",
            style_cell={
                "font-family": "sans-serif",
                "padding": "2px",
            },
            editable=False,
            style_data_conditional=[
                {
                    "if": {
                        "column_id": "ros_order_status",
                        "filter_query": "{ros_order_status} = 'To do'",
                    },
                    "backgroundColor": "tomato",
                    "color": "white",
                },
                {
                    "if": {
                        "column_id": "ros_order_status",
                        "filter_query": "{ros_order_status} = Complete or "
                        " {ros_order_status} = 'Awaiting results'",
                    },
                    "backgroundColor": "green",
                    "color": "white",
                },
                {
                    "if": {
                        "column_id": "mrsa_order_status",
                        "filter_query": "{mrsa_order_status} = 'To do'",
                    },
                    "backgroundColor": "tomato",
                    "color": "white",
                },
                {
                    "if": {
                        "column_id": "mrsa_order_status",
                        "filter_query": "{mrsa_order_status} = Complete or "
                        " {mrsa_order_status} = 'Awaiting results'",
                    },
                    "backgroundColor": "green",
                    "color": "white",
                },
            ],
        )
    ]
