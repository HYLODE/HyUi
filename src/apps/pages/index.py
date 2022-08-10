"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import html, register_page

register_page(__name__, path="/", name="Home")

REFRESH_INTERVAL = 5 * 60 * 1000  # milliseconds

# landing_notes = dcc.Markdown(
#     """
# ### Welcome to the UCLH critical care sitrep and bed management tool

# Here's what we're working on!

# """
# )

jumbotron = html.Div(
    dbc.Container(
        [
            html.H1("Hy!", className="display-3"),
            html.P(["HyperLocal Bed Demand Forecasting at UCLH"], className="lead"),
            html.Hr(className="my-2"),
            html.P("Funded by NHS-X"),
            html.P(
                dbc.Button("Go to the SitRep", color="primary", href="sitrep/sitrep"),
                className="lead",
            ),
        ],
        fluid=True,
        className="py-3",
    ),
    className="p-3 bg-light rounded-3",
)

# """Principal layout for landing page"""
layout = html.Div(
    [
        # All content here organised as per bootstrap
        # dbc.Row(
        #     dbc.Col(
        #         dbc.Card(
        #             [
        #                 dbc.CardHeader(html.H6("HyperLocal Bed Demand Forecasts")),
        #                 dbc.CardBody(html.Div([landing_notes])),
        #             ],
        #         ),
        #         md=12,
        #     ),
        # ),
        jumbotron,
    ],
    # fluid=True,
)
