from dash import html
import dash_bootstrap_components as dbc
from web.pages.perrt import BPID

building_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}building_radio",
                    className="dbc d-grid d-md-flex justify-content-md-end btn-group",
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

closed_beds_switch = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}closed_beds_switch",
                    className="dbc d-grid d-md-flex justify-content-md-end",
                    inline=True,
                    options=[
                        {"label": "Open beds", "value": False},
                        {"label": "All beds", "value": True},
                    ],
                    value=False,
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)
