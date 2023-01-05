"""
Menu and landing page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page
from flask_login import current_user

from web.pages.login import not_logged_in_div_content
from web.pages.home import BPID, callbacks  # noqa

register_page(__name__, path="/", name="Home")


logged_in_content = html.Div(
    dbc.Row(
        [
            dbc.Col(
                html.H2("Hy!"),
                className="me-3",
                width=2,
            ),
        ],
        className="g-2 p-5 position-absolute translate-middle top-50 start-50",
        justify="center",
    )
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
