"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page
from flask_login import current_user

import apps.pages.home.callbacks
from apps.pages.home import BPID, REFRESH_INTERVAL
from config.settings import settings

register_page(__name__, path="/", name="Home")


jumbotron_not_logged_in = html.Div(
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


dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}dept_data"),
    ]
)


def layout():
    if current_user.is_authenticated or settings.ENV == "dev":
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(id=f"{BPID}daq_bar_t03"),
                            ]
                        ),
                        dbc.Col(
                            [
                                html.Div(id=f"{BPID}daq_bar_gwb"),
                            ]
                        ),
                        dbc.Col(
                            [
                                html.Div(id=f"{BPID}daq_bar_wms"),
                            ]
                        ),
                        # dbc.Col(
                        #     [
                        #         html.Div(id=f"{BPID}daq_bar_nhnn0"),
                        #     ]
                        # ),
                        # dbc.Col(
                        #     [
                        #         html.Div(id=f"{BPID}daq_bar_nhnn1"),
                        #     ]
                        # ),
                        dash_only,
                    ]
                ),
            ]
        )

    else:
        return html.Div(
            [
                jumbotron_not_logged_in,
                dash_only,
            ],
        )
