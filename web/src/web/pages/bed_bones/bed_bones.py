"""
sub-application for Bed Bones
use the base row API to create a skeleton bed table for any ward
"""
import collections
from collections import OrderedDict

import dash_bootstrap_components as dbc
import pandas as pd
import requests

from dash import Input, Output, callback
from dash import dash_table as dt
from dash import html, register_page
from dash.dash_table.Format import Format, Scheme

from web.config import get_settings

register_page(__name__)

BPID = "BONES_"


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
        ward_radio_button,
        card_table,
    ],
)


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    via https://stackoverflow.com/a/30655448/992999
    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            # note recursive
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def get_dict_from_list(llist, kkey, vval):
    """
    Given a list of dictionaries, and a key:value pair, will return the matching
    dictionary
    """
    matches = 0
    for ddict in llist:
        if ddict[kkey] == vval:
            res = ddict
            matches += 1
    if matches == 0:
        return {}
    elif matches == 1:
        return res
    else:
        raise ValueError(f"{matches} matches for {kkey}={vval}; expected only 1")


@callback(
    Output(bed_table, "children"),
    Input(ward_radio, "value"),
)
def gen_bed_table(ward: str):
    data = requests.get(
        f"{get_settings().api_url}/bedbones/beds", params={ward: ward}
    ).json()["results"]

    df = pd.DataFrame.from_records(data)
    COLS = OrderedDict(
        {
            "unit_order": "Unit Order",
            # "location_id": "Location ID",
            "location_string": "Location string",
            # "DepartmentName": "Ward",
            "room": "Room",
            "bed": "Bed",
            "closed": "Closed",
            "covid": "COVID",
        }
    )
    df = df[COLS.keys()]
    df["unit_order"] = df["unit_order"].astype(int, errors="ignore")
    df["closed"] = df["closed"].astype(str)
    df["covid"] = df["covid"].astype(str)

    # Prep columns with ids and names
    COL_DICT = [{"name": v, "id": k} for k, v in COLS.items() if k in COLS]

    deep_update(
        get_dict_from_list(COL_DICT, "id", "unit_order"),
        dict(type="numeric"),
    )
    deep_update(
        get_dict_from_list(COL_DICT, "id", "unit_order"),
        dict(format=Format(precision=0, scheme=Scheme.fixed)),
    )

    return [
        dt.DataTable(
            columns=COL_DICT,
            data=df.to_dict("records"),
            sort_action="native",
            sort_by=[{"column_id": "unit_order", "direction": "asc"}],
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
