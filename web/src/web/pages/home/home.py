import json
import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import requests
from dash import Input, Output, callback, dcc, html

from models.census import CensusRow
from web.config import get_settings

dash.register_page(__name__, path="/", name="Home")


@callback(
    Output("store-census", "data"),
    Input("campus-multi-select", "value"),
    background=True,
)
def _store_census(value: list[str] | str) -> list[dict]:
    if type(value) is str:
        campuses = [value]
    else:
        campuses = value  # type:ignore

    response = requests.get(
        f"{get_settings().api_url}/census/campus/", params={"campuses": campuses}
    )
    return [CensusRow.parse_obj(row).dict() for row in response.json()]


@callback(
    Output("cytoscape-census", "elements"),
    Input("store-census", "data"),
    background=True,
)
def _prepare_cyto_elements(data: list[dict]) -> list[dict]:
    elements = list()
    for d in data:
        d = dict(
            id=d.get("location_string"),
            occupied=d.get("occupied"),
        )
        element = dict(data=d)
        elements.append(element)
    return elements


@callback(
    Output("node-debug", "children"),
    Input("cytoscape-census", "tapNode"),
    prevent_initial_callback=True,
)
def tap_debug_inspector(data: dict) -> str:
    if data:
        data.pop("style", None)
    return json.dumps(data, indent=4)


debug_inspector = html.Div([dmc.Prism(language="python", id="node-debug", children="")])

campus_selector = html.Div(
    [
        dmc.MultiSelect(
            label="Select campus",
            placeholder="Select all you like!",
            id="campus-multi-select",
            value=["WMS"],
            data=["GWB", "NHNN", "UCH", "WMS"],
            style={"width": 400, "marginBottom": 10},
        ),
    ]
)

cyto_style_sheet = [
    {
        "selector": "[?occupied]",
        "style": {
            "background-color": "red",
        },
    },
    {
        "selector": ":selected:",
        "style": {
            "shape": "star",
            "background-color": "blue",
        },
    },
]

census_cyto = cyto.Cytoscape(
    id="cytoscape-census",
    stylesheet=cyto_style_sheet,
)

stores = html.Div(dcc.Store(id="store-census"))

body = html.Div(
    [
        dmc.Container(
            size="lg",
            mt=0,
            children=[
                campus_selector,
                census_cyto,
                debug_inspector,
            ],
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            stores,
            body,
        ]
    )
