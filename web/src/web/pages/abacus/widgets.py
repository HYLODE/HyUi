"""
Plotly dash layout components
"""
import dash_bootstrap_components as dbc
from dash import html

from web.pages.abacus import BPID

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
                    value="tower",
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
                    "justify-content-md-begin btn-group",
                    inline=True,
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

discharge_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}discharge_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Not ready", "value": "no"},
                        {"label": "End of life", "value": "dying"},
                        {"label": "Review", "value": "review"},
                        {"label": "Ready", "value": "ready"},
                    ],
                    # value="no",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)
