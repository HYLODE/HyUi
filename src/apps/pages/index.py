"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import html, register_page


register_page(__name__, path="/", name="Home")


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


def layout():
    return html.Div(
        [
            jumbotron,
        ],
        # fluid=True,
    )
