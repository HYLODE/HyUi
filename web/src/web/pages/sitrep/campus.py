import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
from dash import dcc, html
from pathlib import Path

import web.pages.sitrep.callbacks  # noqa
from web.pages.sitrep import CAMPUSES, ids

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)

dash.register_page(__name__, path="/sitrep", name="Sitrep")

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
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "UCH"][0],
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
            ],
        )
    ]
)

census_cyto = cyto.Cytoscape(
    id=ids.CYTO_MAP,
    style={
        "width": "1000px",
        "height": "600px",
    },
    stylesheet=cyto_style_sheet,
    responsive=True,
    userPanningEnabled=True,
    userZoomingEnabled=True,
)

timers = html.Div([])

stores = html.Div(
    [
        dcc.Store(id=ids.CENSUS_STORE),
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
                dmc.Stack(
                    [
                        campus_selector,
                        layout_selector,
                        census_cyto,
                        debug_inspector,
                    ],
                    style={},
                    align="flex-start",
                    justify="flex-start",
                    spacing="sm",
                )
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
