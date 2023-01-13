import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
import math
from dash import dcc, html
from pathlib import Path

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks  # noqa
from web.pages.sitrep import CAMPUSES, ids

dash.register_page(__name__, path="/sitrep", name="Sitrep")

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)

DEBUG = True
if DEBUG:
    debug_inspector = html.Div(
        [dmc.Prism(language="json", id=ids.DEBUG_NODE_INSPECTOR, children="")]
    )
else:
    debug_inspector = html.Div()

timers = html.Div([])
stores = html.Div(
    [
        dcc.Store(id=ids.CENSUS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE_NAMES),
        dcc.Store(id=ids.ELEMENTS_STORE_CAMPUS),
        dcc.Store(id=ids.ELEMENTS_STORE_WARD),
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
            label="Select a ward",
            placeholder="ward",
            id=ids.DEPT_SELECTOR,
        ),
    ]
)

layout_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.LAYOUT_SELECTOR,
            value="circle",
            data=[
                "preset",
                "grid",
                "circle",
                "random",
            ],
        )
    ]
)

campus_cyto = dmc.Paper(
    [
        dmc.Grid(
            children=[
                dmc.Col(
                    [
                        cyto.Cytoscape(
                            id=ids.CYTO_CAMPUS_CYTO,
                            style={
                                "width": "1000px",
                                "height": "800px",
                                "z-index": 999,
                            },
                            layout={
                                "name": "preset",
                                "animate": True,
                                "fit": True,
                                "padding": 10,
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

ward_cyto = dmc.Paper(
    [
        dmc.Grid(
            children=[
                dmc.Col(
                    [
                        cyto.Cytoscape(
                            id=ids.CYTO_WARD_CYTO,
                            style={
                                "width": "1000px",
                                "height": "800px",
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


def page_status_controls(status: list[dmc.Col], controls: list[dmc.Col]) -> dmc.Paper:
    """Function to define consistent layout to status and controls across
    pages"""
    return dmc.Paper(
        [
            dmc.Grid(
                [
                    *controls,
                    *status,
                ],
                grow=False,
                gutter="m",
            )
        ],
        p="xs",
    )


def tab_status_controls(status: list[dmc.Col], controls: list[dmc.Col]) -> dmc.Paper:
    """Function to define consistent layout to status and controls across
    tabs"""
    return dmc.Paper(
        [
            dmc.Grid(
                [
                    *controls,
                    *status,
                ],
                grow=False,
                gutter="m",
            )
        ],
        p="xs",
    )


tab_panel_campus = html.Div(
    [
        dmc.TabsPanel(
            children=[
                tab_status_controls(
                    controls=[
                        # dmc.Col(layout_selector, span=4),
                        dmc.Col("campus control placeholder text", span=4),
                        dmc.Col("campus control placeholder text", span=2),
                    ],
                    status=[
                        dmc.Col("campus status placeholder text", span=2),
                    ],
                ),
                dmc.Stack(
                    [
                        campus_cyto,
                        # debug_inspector,
                    ],
                    style={},
                    align="flex-start",
                    justify="center",
                    spacing="sm",
                ),
            ],
            value="campus",
        ),
    ]
)

tab_panel_ward = html.Div(
    [
        dmc.TabsPanel(
            children=[
                tab_status_controls(
                    controls=[
                        dmc.Col(layout_selector, span=4),
                        dmc.Col("ward control placeholder text", span=2),
                    ],
                    status=[
                        dmc.Col("ward status placeholder text", span=2),
                    ],
                ),
                dmc.Stack(
                    [
                        ward_cyto,
                        debug_inspector,
                    ],
                    style={},
                    align="flex-start",
                    justify="flex-start",
                    spacing="sm",
                ),
            ],
            value="ward",
        ),
    ]
)

tabs = html.Div(
    [
        dmc.Tabs(
            children=[
                dmc.TabsList(
                    [
                        dmc.Tab("Campus", value="campus"),
                        dmc.Tab("Ward", value="ward"),
                        dmc.Tab("Bed", value="bed"),
                    ]
                ),
                tab_panel_campus,
                tab_panel_ward,
                dmc.TabsPanel("this bed", value="bed"),
            ],
            id=ids.TAB_SELECTOR,
            value="campus",
        ),
    ]
)

body = html.Div(
    [
        page_status_controls(
            controls=[
                dmc.Col(campus_selector),
                dmc.Col(dept_selector),
            ],
            status=[],
        ),
        tabs,
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
