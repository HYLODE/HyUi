"""
sub-application for ros
"""
from typing import Any

import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, callback, register_page
from dash import dash_table as dt
from dash import dcc, html
from flask_login import current_user

from datetime import datetime, date, timedelta

from models.ros import RosRead
from web.config import get_settings

register_page(__name__, name="ROS")
BPID = "ROS_"


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


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])
    return html.Div(
        [
            ward_radio_button,
            card_table,
            # pie_chart := dcc.Graph(),
            dash_only,
        ],
    )


def format_datetime(d):
    if not d:
        return ""
    return d.strftime("%d/%m/%y %H:%M")


def from_isodate(d):
    if not d:
        return None
    return datetime.fromisoformat(d)


def create_and_format_date(st):
    return format_datetime(from_isodate(st))


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
def store_data(n_intervals: int) -> dict[str, Any]:
    """
    Read data from API then store as JSON
    """

    response = requests.get(f"{get_settings().api_url}/ros/")
    data = [RosRead.parse_obj(row) for row in response.json()]

    pts_by_department: dict[
        str, Any
    ] = dict()  # stores the patient lists keyed on the department name

    for row in data:
        # Format admission date for table
        admission_time = from_isodate(row["hospital_admission_datetime"])
        row["admission_time_str"] = admission_time.strftime("%d/%m/%y %H:%M")

        row["ros_order_status"] = "To do"
        row["mrsa_order_status"] = "To do"

        row["ros_orders_tooltip"] = ""
        row["mrsa_orders_tooltip"] = ""
        row["covid_orders_tooltip"] = ""

        if row["ros_orders"]:
            ros_orders = row["ros_orders"]

            most_recent_order = ros_orders[0]
            recent_order_datetime = from_isodate(most_recent_order["order_datetime"])

            row["ros_order_datetime_str"] = format_datetime(recent_order_datetime)

            if (
                recent_order_datetime.date() >= admission_time.date()
            ):  # If a test has been ordered during this admission
                if (
                    most_recent_order["result_status"] is not None
                ):  # And there is a result back: screening complete
                    row["ros_order_status"] = "Complete"
                else:  # If there is no result, we are awaiting results
                    row["ros_order_status"] = "Awaiting results"

            temp_str = "\n\n".join(
                [
                    (
                        f"{create_and_format_date(x['order_datetime'])}; "
                        f"{x['result_status']}; "
                        f"{x['abnormal_flag'] if x['abnormal_flag'] else ''} "
                    )
                    for x in ros_orders
                ]
            )

            row[
                "ros_orders_tooltip"
            ] = f"{row['firstname']} {row['lastname']} – ROS\n\n{temp_str}"

        if row["mrsa_orders"]:

            mrsa_orders = row["mrsa_orders"]

            most_recent_order = mrsa_orders[0]

            recent_order_datetime = from_isodate(most_recent_order["order_datetime"])

            row["mrsa_order_datetime_str"] = format_datetime(recent_order_datetime)

            row["mrsa_order_status"] = "To do"

            if recent_order_datetime.date() >= (
                date.today() - timedelta(7)
            ):  # If MRSA screening done in last 7 days
                if (
                    most_recent_order["result_status"] is not None
                ):  # And we have a result, then we are finished
                    row["mrsa_order_status"] = "Complete"
                else:  # Else we are awaiting results
                    row["mrsa_order_status"] = "Awaiting results"

            temp_str = "\n\n".join(
                [
                    (
                        f"{create_and_format_date(x['order_datetime'])}; "
                        f"{x['result_status']}; "
                        f"{x['abnormal_flag'] if x['abnormal_flag'] else ''}"
                    )
                    for x in mrsa_orders
                ]
            )

            row[
                "mrsa_orders_tooltip"
            ] = f"{row['firstname']} {row['lastname']} – MRSA\n\n{temp_str}"

        if row["covid_orders"]:

            covid_orders = row["covid_orders"]

            most_recent_order = covid_orders[0]
            recent_order_datetime = from_isodate(most_recent_order["order_datetime"])

            row["covid_order_datetime_str"] = (
                f"{format_datetime(recent_order_datetime)}; "
                f"({abs((recent_order_datetime.date() - date.today()).days)} days ago)"
            )

            temp_str = "\n\n".join(
                [
                    (
                        f"{create_and_format_date(x['order_datetime'])}; "
                        f"{x['result_status']}; "
                        f"{x['abnormal_flag'] if x['abnormal_flag'] else ''}"
                    )
                    for x in covid_orders
                ]
            )

            row[
                "covid_orders_tooltip"
            ] = f"{row['firstname']} {row['lastname']} – COVID PCR\n\n{temp_str}"

        # Add data to the individual department list
        dept_list = pts_by_department.get(row["department"], [])
        dept_list.append(row)

        # TODO: Must fix typing here.
        dept_list = sorted(dept_list, key=lambda d: d["bed_name"])  # type: ignore
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
        covid_order_datetime_str="Last COVID19 PCR order",
    )

    return [
        dt.DataTable(
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data.get(ward, []),
            tooltip_data=[
                {
                    "ros_order_datetime_str": {
                        "value": row["ros_orders_tooltip"],
                        "type": "markdown",
                    },
                    "mrsa_order_datetime_str": {
                        "value": row["mrsa_orders_tooltip"],
                        "type": "markdown",
                    },
                    "covid_order_datetime_str": {
                        "value": row["covid_orders_tooltip"],
                        "type": "markdown",
                    },
                }
                for row in data.get(ward, [])
            ],
            tooltip_delay=0,
            tooltip_duration=None,
            style_as_list_view=True,
            sort_action="native",
            style_cell={
                "font-family": "sans-serif",
                "padding": "2px",
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
            },
            css=[
                {
                    "selector": ".dash-spreadsheet table",
                    "rule": """
                    table-layout:fixed;
                    width:100%;
                """,
                }
            ],
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