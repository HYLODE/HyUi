"""
Layout for sub-application for the abacus endpoint
"""

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import dcc, html, register_page

import web.pages.abacus.callbacks  # noqa: F401
from web.pages.abacus import BPID, PAGE_REFRESH_INTERVAL, styles
from web.pages.abacus.widgets import (
    building_radio_button,
    discharge_radio_button,
    layout_radio_button,
)

register_page(__name__, name="ABACUS")

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}page_interval",
            interval=PAGE_REFRESH_INTERVAL,
            n_intervals=0,
        ),
        dcc.Store(id=f"{BPID}departments"),
        dcc.Store(id=f"{BPID}census"),
        dcc.Store(id=f"{BPID}beds"),
        dcc.Store(id=f"{BPID}sitrep"),
        dcc.Store(id=f"{BPID}patients_in_beds"),
        dcc.Store(id=f"{BPID}tap_node"),
        dcc.Store(id=f"{BPID}patient_details"),
        dcc.Store(id=f"{BPID}discharge_update"),
    ]
)

bed_inspector = html.Pre(id=f"{BPID}bed_inspector", style=styles["pre"])

# using the term 'form' to indicate that this is for user input
discharge_form = html.Div(
    [
        discharge_radio_button,
        html.Div(
            [
                dbc.Button(
                    "Submit",
                    id=f"{BPID}discharge_submit_button",
                    className="dbc d-grid d-md-flex justify-content-md-end "
                    "btn-group",
                    size="sm",
                    color="primary",
                    disabled=True,
                ),
            ],
            className="dbc d-grid d-md-flex justify-content-md-end",
        ),
    ]
)

patient_inspector = dcc.Loading(
    html.Pre(id=f"{BPID}patient_inspector", style=styles["pre"])
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
                    dbc.Col([layout_radio_button]),
                    dbc.Col([building_radio_button]),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(id=f"{BPID}dept_title"),
                            ward_map,
                        ],
                        # width={"size": 6, "order": "first", "offset": 6},
                    ),
                    dbc.Col(
                        [
                            html.Div(id=f"{BPID}dept_dropdown_div"),
                            html.Div(
                                id=f"{BPID}node_inspector",
                                children=[
                                    bed_inspector,
                                    discharge_form,
                                    patient_inspector,
                                ],
                                hidden=True,
                            ),
                        ],
                        # width={"size": 6, "order": "last", "offset": 6},
                    ),
                ]
            ),
            html.Div(id=f"{BPID}ward_map"),
            dash_only,
        ]
    )
