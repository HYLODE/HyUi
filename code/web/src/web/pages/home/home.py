"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page
from flask_login import current_user

from web.pages.home import BPID

from web.pages.home import callbacks  # noqa

register_page(__name__, path="/", name="Home")


not_logged_in_div_content = html.Div(
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

logged_in_content = dbc.Row(
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
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=1000 * 60 * 15, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}dept_data"),
    ]
)

logged_in_container = html.Div([logged_in_content, dash_only])
not_logged_in_container = html.Div([not_logged_in_div_content, dash_only])


def layout():
    if current_user.is_authenticated:
        return logged_in_container
    return not_logged_in_container
