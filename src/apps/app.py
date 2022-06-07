# src/apps/app.py
"""
The application itself
"""
from dash import Dash
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    title="HyUi",
    update_title=None,
    external_stylesheets=[
        dbc.themes.FLATLY,
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
)
server = app.server
