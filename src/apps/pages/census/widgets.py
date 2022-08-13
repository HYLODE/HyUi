# src/apps/pages/census/widgets.py
from dash import html
import dash_bootstrap_components as dbc
from apps.pages.census import BPID

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
