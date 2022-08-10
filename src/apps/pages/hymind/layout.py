# src/apps/pages/hymind/hymind.py
"""
Sub-application for HyMind
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from apps.pages.hymind import BPID, REFRESH_INTERVAL

card_el_tap = dbc.Card(
    [
        dbc.CardHeader(html.H6("Elective tap")),
        dbc.CardBody(
            [
                html.Div(id=f"{BPID}el_tap_fig"),
                # html.Div([html.P("Elective Tap")]),
            ]
        ),
    ]
)

card_em_tap = dbc.Card(
    [
        dbc.CardHeader(html.H6("Emergency tap")),
        dbc.CardBody(
            [
                html.Div(id=f"{BPID}em_tap_fig"),
                # html.Div([html.P("Emergency Tap")]),
            ]
        ),
    ]
)

main_layout = html.Div(
    [
        card_em_tap,
        card_el_tap,
        # html.Div([html.P("Read these by choosing the ris")]),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query_interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}em_tap_data"),
        dcc.Store(id=f"{BPID}el_tap_data"),
    ]
)


def layout():
    return html.Div(
        [
            main_layout,
            dash_only,
        ]
    )
