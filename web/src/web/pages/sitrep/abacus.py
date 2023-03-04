import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
from dash import html
from pathlib import Path

import web.pages.sitrep.callbacks.abacus  # noqa

from web.pages.sitrep import ids
from web.style import replace_colors_in_stylesheet
from web import SITREP_DEPT2WARD_MAPPING

dash.register_page(__name__, path="/sitrep/abacus", name="Abacus")

with open(Path(__file__).parent / "abacus_style.json") as f:
    abacus_style = json.load(f)
    abacus_style = replace_colors_in_stylesheet(abacus_style)

timers = html.Div([])
stores = html.Div([])

dept_selector = dmc.Container(
    [
        dmc.SegmentedControl(
            id=ids.DEPT_SELECTOR,
            value="UCH T03 INTENSIVE CARE",
            data=[
                {"value": k, "label": v}
                for k, v in list(SITREP_DEPT2WARD_MAPPING.items())
            ],
        ),
    ],
)

abacus = dmc.Paper(
    [
        cyto.Cytoscape(
            id=ids.ABACUS_CHART,
            style={
                # "width": "70vw",
                "height": "70vh",
                "z-index": 999,
            },
            layout={
                "name": "preset",
                "animate": True,
                "fit": True,
                "padding": 10,
            },
            stylesheet=abacus_style,
            responsive=True,
            userPanningEnabled=True,
            userZoomingEnabled=True,
        )
    ],
    shadow="lg",
    radius="lg",
    p="md",  # padding
    withBorder=True,
    # style={"width": "90vw"},
)

body = dmc.Container(
    [
        dmc.Grid(
            [
                dmc.Col(dept_selector, offset=9, span=3),
                dmc.Col(abacus, span=12),
            ]
        ),
    ],
    style={"width": "90vw"},
    fluid=True,
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
        ]
    )
