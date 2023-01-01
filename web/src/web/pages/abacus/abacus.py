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

# bed_inspector = html.Pre(id=f"{BPID}bed_inspector", style=styles["pre"])
bed_inspector = dbc.Card(
    [
        dbc.CardHeader(html.H3(id=f"{BPID}bed_inspector_header")),
        dbc.CardBody(html.P(id=f"{BPID}bed_inspector_body")),
    ]
)

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
                {
                    "selector": "[?closed]",
                    "style": {
                        "shape": "polygon",
                        "shape-polygon-points": "-1 1 1 1 1 -1 -1 -1 -1 1 0.9 -0.9"
                        # "background-color": "black",
                        # "background-opacity": 0.2,
                        # "border-width": 1,
                        # "border-style": "solid",
                        # "border-color": "red",
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

_summ_col = ("border rounded border-light border-1 p-2",)
_summ_slider_div = "hstack gap-3"
_summ_slider_label = "w-25 text-end"


def layout():
    return dbc.Container(
        [
            dbc.Row(
                id=f"{BPID}ward_status",
                children=[
                    # Status summary row
                    # ==================
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Admissions", className="text-begin"),
                                ],
                                className="hstack p-0",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Confirmed",
                                        className=_summ_slider_label,
                                    ),
                                    dcc.Slider(
                                        id=f"{BPID}adm_confirmed",
                                        min=0,
                                        max=5,
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
                                className=_summ_slider_div + "pb-0",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Expected",
                                        className=_summ_slider_label,
                                    ),
                                    dcc.Slider(
                                        id=f"{BPID}adm_expected",
                                        min=0,
                                        max=5,
                                        step=1,
                                        value=1,
                                        marks=None,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className=_summ_slider_div + "pt-0",
                            ),
                        ],
                        width=3,
                        className=_summ_col,
                    ),
                    dbc.Col(
                        children=[
                            html.Div(
                                [
                                    html.H5("Ward occupancy", className="text-begin"),
                                ],
                                className="hstack p-0",
                            ),
                            html.Div(
                                [
                                    html.P("Now", className="w-20 text-end"),
                                    dcc.Slider(
                                        id=f"{BPID}pts_now_slider",
                                        min=0,
                                        step=1,
                                        marks=None,
                                        disabled=False,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className=_summ_slider_div + "pb-0",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Next", className="fw-bold w-20 " "text-end"
                                    ),
                                    dcc.RangeSlider(
                                        id=f"{BPID}pts_next_slider",
                                        step=1,
                                        marks=None,
                                        allowCross=False,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className=_summ_slider_div + "pt-0",
                            ),
                        ],
                        width=6,
                        className=_summ_col,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H5("Discharges", className=""),
                                ],
                                className="hstack p-0",
                            ),
                            html.Div(
                                [
                                    html.P("Ready", className=_summ_slider_label),
                                    dcc.Slider(
                                        id=f"{BPID}dcs_ready",
                                        min=0,
                                        step=1,
                                        marks=None,
                                        disabled=True,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": True,
                                        },
                                        className="w-100",
                                    ),
                                ],
                                className=_summ_slider_div + "pb-0",
                            ),
                            html.Div(
                                [
                                    html.P("Confirmed", className=_summ_slider_label),
                                    dcc.Slider(
                                        id=f"{BPID}dcs_confirmed",
                                        min=0,
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
                                className=_summ_slider_div + "pt-0",
                            ),
                        ],
                        width=3,
                        className=_summ_col,
                    ),
                ],
                className="border rounded bg-light",
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
                className="border rounded p-3 bg-light",
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
                            html.Div(
                                id=f"{BPID}node_inspector",
                                children=[
                                    bed_inspector,
                                    discharge_form,
                                    # patient_inspector,
                                ],
                                hidden=True,
                            ),
                            html.Div([node_debug]),
                        ],
                    ),
                ],
                className="border rounded p-3",
            ),
            html.Div(id=f"{BPID}ward_map"),
            dash_only,
        ],
        className="dbc",
        fluid=True,
    )
