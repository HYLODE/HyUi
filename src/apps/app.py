# src/apps/app.py
"""
The application itself
"""
from dash import Dash, Input, Output, dcc, html, callback
import dash_bootstrap_components as dbc

from index import home_page
from consults.consults import consults

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


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return landing
    elif pathname == "/consults":
        return consults
    else:
        # TODO proper 404  route
        return "404"


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8095, debug=True)
