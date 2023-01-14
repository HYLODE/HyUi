import math
import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
from dash import dcc, html
from pathlib import Path

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks  # noqa
from web.pages.sitrep import CAMPUSES, ids
from web.pages.sitrep.widgets import page_status_controls
from web.style import replace_colors_in_stylesheet, AppColors


dash.register_page(__name__, path="/sitrep/ward", name="Ward")

colors = AppColors()

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)
    cyto_style_sheet = replace_colors_in_stylesheet(cyto_style_sheet)


timers = html.Div([])
stores = html.Div(
    [
        dcc.Store(id=ids.CENSUS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE_NAMES),
    ]
)

campus_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.CAMPUS_SELECTOR,
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "UCH"][0],
            data=CAMPUSES,
        ),
    ]
)

dept_selector = html.Div(
    [
        dmc.Select(
            # label="Select a ward",
            placeholder="Select a ward",
            id=ids.DEPT_SELECTOR,
            searchable=True,
            nothingFound="No match found",
        ),
    ]
)

ward_cyto = dmc.Paper(
    [
        dmc.Grid(
            children=[
                dmc.Col(
                    [
                        cyto.Cytoscape(
                            id=ids.CYTO_WARD,
                            style={
                                "width": "70vw",
                                "height": "70vh",
                                "z-index": 999,
                            },
                            layout={
                                "name": "circle",
                                "animate": True,
                                "fit": True,
                                "padding": 10,
                                "startAngle": math.pi
                                * 2
                                / 3,  # clockwise from 3 O'Clock
                                "sweep": math.pi * 5 / 3,
                            },
                            stylesheet=cyto_style_sheet,
                            responsive=True,
                            userPanningEnabled=True,
                            userZoomingEnabled=True,
                        )
                    ],
                    span=12,
                )
            ],
            grow=True,
        )
    ],
    shadow="lg",
    radius="lg",
    p="md",  # padding
    withBorder=True,
)

debug_inspector = html.Div(
    [dmc.Prism(language="json", id=ids.DEBUG_NODE_INSPECTOR_WARD, children="")]
)

inspector = html.Div(
    [
        dmc.Modal(
            title="Inspect this",
            id=ids.INSPECTOR_WARD,
            centered=True,
            size="60vw",
            overflow="inside",
            overlayColor=colors.gray,
            transition="pop",
            transitionDuration=300,
            children=[debug_inspector],
        )
    ]
)

body = html.Div(
    [
        page_status_controls(
            controls=[
                dmc.Col(campus_selector, span=3),
                dmc.Col(dept_selector, span="auto"),
            ],
            status=[],
        ),
        dmc.Stack(
            [
                ward_cyto,
            ],
            style={},
            align="flex-start",
            justify="flex-start",
            spacing="sm",
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
            inspector,
        ]
    )
