"""
Layout for sub-application for the abacus endpoint
"""

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import dcc, html, register_page

import web.pages.abacus.callbacks  # noqa: F401
from web.pages.abacus import BPID, styles

register_page(__name__, name="ABACUS")

DEPARTMENTS = [
    "WMS W01 CRITICAL CARE",
    "GWB L01 CRITICAL CARE",
    "UCH T03 INTENSIVE CARE",
]
DEPARTMENT = DEPARTMENTS[2]
BUILDING = "tower"
REFRESH_INTERVAL = 10 * 60 * 1000  # 10 mins in milliseconds

building_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}building_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Tower", "value": "tower"},
                        {"label": "GWB", "value": "gwb"},
                        {"label": "WMS", "value": "wms"},
                        {"label": "NHNN", "value": "nhnn"},
                    ],
                    value=BUILDING,
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

layout_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}layout_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Map", "value": "preset"},
                        {"label": "Circle", "value": "circle"},
                        {"label": "Grid", "value": "grid"},
                    ],
                    value="circle",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

bed_inspector = html.Pre(id=f"{BPID}bed_inspector", style=styles["pre"])
# node_inspector = html.Pre(id=f"{BPID}node_inspector")

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query_interval",
            interval=REFRESH_INTERVAL,
            n_intervals=0,
        ),
        dcc.Store(id=f"{BPID}departments"),
        dcc.Store(id=f"{BPID}census"),
        dcc.Store(id=f"{BPID}beds"),
        # dcc.Store(id=f"{BPID}sitrep"),
        dcc.Store(id=f"{BPID}patients_in_beds"),
    ]
)

ward_map = html.Div(
    [
        cyto.Cytoscape(
            id=f"{BPID}bed_map",
            style={
                # "width": "600px",
                # "height": "600px",
                "width": "42vw",
                "height": "80vh",
                "position": "relative",
                "top": "4vh",
                "left": "4vw",
            },
            stylesheet=[
                {"selector": "node", "style": {"label": "data(label)"}},
                {
                    "selector": "[?occupied]",
                    "style": {
                        "shape": "ellipse",
                        # "background-color": "#ff0000",
                        # "background-opacity": 1.0,
                        "border-width": 2,
                        "border-style": "solid",
                        "border-color": "red",
                    },
                },
                {
                    "selector": '[!occupied][level="bed"]',
                    "style": {
                        "shape": "rectangle",
                        "background-color": "grey",
                        "background-opacity": 0.2,
                        "border-width": 2,
                        "border-style": "solid",
                        "border-color": "black",
                    },
                },
                {
                    "selector": '[!visible][level="room"]',
                    "style": {
                        "background-opacity": 0.0,
                        "border-opacity": 0.0,
                    },
                },
            ],
            responsive=True,
            maxZoom=1.0,
            # zoom=1,
            minZoom=0.2,
        )
    ]
)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # html.Div("Row 1 Column 1"),
                            html.Div(id=f"{BPID}dept_title"),
                            # html.Div(id=f"{BPID}ward_map"),
                            ward_map,
                        ],
                        # width={"size": 6, "order": "first", "offset": 6},
                    ),
                    dbc.Col(
                        [
                            building_radio_button,
                            layout_radio_button,
                            html.Div(id=f"{BPID}dept_dropdown_div"),
                            bed_inspector,
                            # node_inspector,
                        ],
                        # width={"size": 6, "order": "last", "offset": 6},
                    ),
                ]
            ),
            html.Div(id=f"{BPID}ward_map"),
            dash_only,
        ]
    )
