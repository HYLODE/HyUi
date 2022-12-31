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
    department_dropdown,
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
        dcc.Store(id=f"{BPID}discharge_statuses"),
        dcc.Store(id=f"{BPID}elements"),
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

node_debug = dcc.Loading(html.Pre(id=f"{BPID}node_debug", style=styles["pre"]))

ward_map = html.Div(
    [
        cyto.Cytoscape(
            id=f"{BPID}bed_map",
            style={
                "width": "42vw",
                "height": "70vh",
                "position": "relative",
                "top": "1vh",
                "left": "1vw",
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
                    "selector": '[?discharge][level="bed"]',
                    "style": {
                        "shape": "star",
                        # "background-color": "grey",
                        # "background-opacity": 0.2,
                        # "border-width": 2,
                        # "border-style": "solid",
                        # "border-color": "black",
                    },
                },
            ],
            # autoRefreshLayout=True,
            responsive=True,
            maxZoom=1.0,
            # zoom=1,
            minZoom=0.2,
        )
    ]
)


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    # Status summary row
                    # ==================
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.P(
                                        "Known admissions", className="w-100 text-end"
                                    ),
                                    dcc.Slider(
                                        id=f"{BPID}show_adm_now_n",
                                        min=0,
                                        max=6,
                                        step=1,
                                        value=0,
                                        marks=None,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className="hstack gap-3 pb-0",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Unknown admissions", className="w-100 text-end"
                                    ),
                                    dcc.Slider(
                                        id=f"{BPID}show_adm_nxt_n",
                                        min=0,
                                        max=6,
                                        step=1,
                                        value=0,
                                        marks=None,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className="hstack gap-3 pt-0",
                            ),
                        ],
                        className="border rounded border-warning border-3 p-3",
                    ),
                    dbc.Col(
                        [html.Div(id=f"{BPID}show_pts_now_n")],
                        className="border rounded border-warning border-3",
                    ),
                    dbc.Col(
                        [html.Div(id=f"{BPID}show_dcs_now_n")],
                        className="border rounded border-danger border-3",
                    ),
                ],
                className="border rounded m-1",
            ),
            dbc.Row(
                [
                    # Department and map menu row
                    # ===========================
                    dbc.Col(
                        [
                            building_radio_button,
                        ]
                    ),
                    dbc.Col(
                        [
                            # html.Div(id=f"{BPID}dept_dropdown_div"),
                            department_dropdown,
                        ]
                    ),
                    dbc.Col([layout_radio_button]),
                ],
                className="border rounded m-1 bg-light",
            ),
            dbc.Row(
                [
                    # Map and patient inspector row
                    # =============================
                    dbc.Col(
                        [
                            html.Div(id=f"{BPID}dept_title"),
                            ward_map,
                        ]
                    ),
                    dbc.Col(
                        [
                            # html.Div([node_debug]),
                            html.Div(
                                id=f"{BPID}node_inspector",
                                children=[
                                    bed_inspector,
                                    discharge_form,
                                    patient_inspector,
                                ],
                                hidden=True,
                            )
                        ],
                    ),
                ],
                className="border rounded m-1",
            ),
            html.Div(id=f"{BPID}ward_map"),
            dash_only,
        ],
        className="dbc",
    )
