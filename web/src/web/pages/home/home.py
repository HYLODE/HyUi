import json

import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
from dash import dcc, html

from web.pages.home import ids
import web.pages.home.callbacks  # noqa
from pathlib import Path

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)


dash.register_page(__name__, path="/", name="Home")

debug_inspector = html.Div(
    [dmc.Prism(language="json", id=ids.DEBUG_NODE_INSPECTOR, children="")]
)

campus_selector = html.Div(
    [
        dmc.MultiSelect(
            label="Select campus",
            placeholder="Select all you like!",
            id=ids.CAMPUS_SELECTOR,
            value=["WMS"],
            data=["GWB", "NHNN", "UCH", "WMS"],
            style={"width": 400, "marginBottom": 10},
        ),
    ]
)

layout_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.LAYOUT_SELECTOR,
            value="grid",
            data=[
                "grid",
                "circle",
                "random",
            ],
        )
    ]
)

census_cyto = cyto.Cytoscape(
    id=ids.CYTO_MAP,
    stylesheet=cyto_style_sheet,
    responsive=True,
)

timers = html.Div([])

stores = html.Div(
    [
        dcc.Store(id=ids.CENSUS_STORE),
        dcc.Store(id=ids.ROOM_SET_STORE),
        dcc.Store(id=ids.DEPT_SET_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
    ]
)


body = html.Div(
    [
        dmc.Container(
            size="lg",
            mt=0,
            children=[
                campus_selector,
                layout_selector,
                census_cyto,
                debug_inspector,
            ],
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
        ]
    )
