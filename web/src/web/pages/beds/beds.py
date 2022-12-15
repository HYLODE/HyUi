"""
sub-application for Beds
use the base row API to create a skeleton bed table for any ward
"""
from collections import OrderedDict

import dash_bootstrap_components as dbc

import requests

from dash import Input, Output, callback
from dash import dash_table as dt
from dash import html, register_page

from web.config import get_settings

from models.beds import Bed
from web.convert import parse_to_data_frame

register_page(__name__)


department_radio_button = html.Div(
    [
        html.Div(
            [
                department_radio := dbc.RadioItems(
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
        dbc.CardHeader(html.H5("Beds Demo")),
        dbc.CardBody(
            [
                bed_table := html.Div(),
            ]
        ),
    ]
)


layout = html.Div(
    [
        department_radio_button,
        card_table,
    ],
)


@callback(
    Output(bed_table, "children"),
    Input(department_radio, "value"),
)
def gen_bed_table(department: str):

    columns = OrderedDict(
        {
            "location_string": "Location String",
            "room": "Room",
            "bed": "Bed",
            "closed": "Closed",
            "covid": "COVID",
        }
    )

    response = requests.get(
        f"{get_settings().api_url}/beds/", params={"department": department}
    )

    df = parse_to_data_frame(response.json(), Bed)
    df = df[columns.keys()]
    df["closed"] = df["closed"].astype(str)
    df["covid"] = df["covid"].astype(str)

    return [
        dt.DataTable(
            columns=[{"name": v, "id": k} for k, v in columns.items() if k in columns],
            data=df.to_dict("records"),
            sort_action="native",
            style_cell={
                "font-family": "sans-serif",
                "padding": "2px",
            },
            editable=False,
            style_data_conditional=[
                {
                    "if": {
                        "column_id": "closed",
                        "filter_query": "{closed} = 'True'",
                    },
                    "backgroundColor": "tomato",
                    "color": "white",
                },
                {
                    "if": {
                        "column_id": "covid",
                        "filter_query": "{covid} = 'True'",
                    },
                    "backgroundColor": "#FF4136",
                    "color": "white",
                },
            ],
        )
    ]
