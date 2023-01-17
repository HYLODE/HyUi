"""
sub-application for the demo endpoint
"""
from datetime import datetime
from typing import Any, List, Dict

import requests
from dash import Input, Output, callback, register_page
from dash import dash_table as dt
from dash import dcc, html

from web.config import get_settings

register_page(__name__, name="DEMO")
# prefix to name space all objects on this page
BPID = "DEMO_"
REFRESH_INTERVAL = 6 * 60 * 60 * 1000  # milliseconds

# Components of the layout
# ========================

# hidden element on the web page that holds dash components used to trigger refreshes and to hold
# data
dash_only = html.Div(
    [
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        request_data := dcc.Store(id=f"{BPID}request_data"),
    ]
)

# section at the top of the page before the data table
page_intro = html.Div(
    [
        html.H3(["Demonstration table"]),
        dcc.Markdown(
            """
    The table below is populated by a *get* request to
    - [http://localhost:8200/demo/?days_ahead=1]() on the live system
    - [http://localhost:8200/mock/demo/]() on the mock (local/development) system

    """
        ),
    ]
)

# the (data) table to be displayed
main_table = html.Div(
    [
        demo_table := html.Div(),
    ]
)


# Plotly dash looks for an object named layout and uses this to build the page
def layout():
    """
    function to hold the plotly dash layout
    """
    return html.Div(
        [
            page_intro,
            main_table,
            dash_only,
        ]
    )


# noinspection PyUnusedLocal
@callback(Output(request_data, "data"), Input(query_interval, "n_intervals"))
def store_data(n_intervals: int) -> dict[str, Any]:
    """
    Read the data from the backend endpoint and store in the frontend web
    application (not directly visible to the user)

    :param n_intervals: only used to trigger the callback
    :return: json dictionary of data from the request
    """
    return requests.get(f"{get_settings().api_url}/demo").json()


def _prettify_datetime(s: str) -> str:
    """Private method to format string"""
    s = datetime.fromisoformat(s).strftime("%a %d %b")
    return s


@callback(Output(demo_table, "children"), Input(request_data, "data"))
def gen_data_table(data: List[Dict]):
    """
    build the data table

    :param data: json data stored locally
    :return: Plotly Datatable
    """

    for i in data:
        i["operation_date"] = _prettify_datetime(i.get("SurgeryDateClarity"))

    # Use this dictionary to convert json/dataframe columns into nice headings
    cols = dict(
        pod_orc="Post-operative destination",
        or_case_id="OR Case ID",
        operation_date="Operation date",
    )

    return [
        dt.DataTable(
            columns=[
                {
                    "id": "pod_orc",
                    "name": cols.get("pod_orc"),
                    "type": "text",
                },
                {
                    "id": "or_case_id",
                    "name": cols.get("or_case_id"),
                    "type": "numeric",
                },
                {
                    "id": "operation_date",
                    "name": cols.get("operation_date"),
                    "type": "text",
                },
            ],
            data=data,
            style_cell={"textAlign": "left"},  # CSS styling dictionary
            sort_action="native",
            filter_action="native",
        )
    ]
