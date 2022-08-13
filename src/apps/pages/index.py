"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import html, register_page, dcc


register_page(__name__, path="/", name="Home")


jumbotron = html.Div(
    dbc.Container(
        [
            dcc.Markdown(
                """
                Hi there!
            """,
                className="display-3",
            ),
            dcc.Markdown(
                """
                ... or even _Hy there!_
            """
            ),
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
