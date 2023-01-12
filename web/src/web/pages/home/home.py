import json

import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
from dash import dcc, html

from web.pages.home import CAMPUSES
from web.pages.home import ids
import web.pages.home.callbacks  # noqa
from pathlib import Path

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)


dash.register_page(__name__, path="/", name="Home")

DEBUG = True
if DEBUG:
    debug_inspector = html.Div(
        [dmc.Prism(language="json", id=ids.DEBUG_NODE_INSPECTOR, children="")]
    )
else:
    debug_inspector = html.Div()


campus_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.CAMPUS_SELECTOR,
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "WMS"][0],
            data=CAMPUSES,
        ),
    ]
)

layout_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.LAYOUT_SELECTOR,
            value="preset",
            data=[
                "preset",
                "grid",
                "circle",
                "random",
                # "concentric",
                # "breadthfirst",
                # "cose",
            ],
        )
    ]
)

census_cyto = cyto.Cytoscape(
    id=ids.CYTO_MAP,
    style={
        "width": "80vw",
        "height": "50vh",
    },
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
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
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
