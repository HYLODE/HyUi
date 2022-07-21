"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, page_registry

register_page(__name__, path="/", name="Home")

REFRESH_INTERVAL = 5 * 60 * 1000  # milliseconds

landing_notes = dcc.Markdown(
    """
### Welcome to the UCLH critical care sitrep and bed management tool

Here's what we're working on!

"""
)

# """Principal layout for landing page"""
layout = html.Div(
    [
        # All content here organised as per bootstrap
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H6("HyperLocal Bed Demand Forecasts")),
                        dbc.CardBody(html.Div([landing_notes])),
                    ],
                ),
                md=12,
            ),
        ),
    ],
    # fluid=True,
)
