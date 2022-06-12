# src/apps/app.py
"""
The application itself
"""
from dash import Dash, Input, Output, dcc, html, callback
import dash_bootstrap_components as dbc

from config import settings
from apps.index import home_page
from apps.consults.consults import consults
from apps.sitrep.sitrep import sitrep

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


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return home_page
    elif pathname == "/consults":
        return consults
    elif pathname == "/sitrep":
        return sitrep
    else:
        # TODO proper 404  route
        return "404"


# standalone apps : please use ports fastapi 8092 and dash 8093
# this is the callable object run by gunicorn
# cd ./src/
# gunicorn -w 4 --bind 0.0.0.0:8093 apps.app:server
server = app.server


# this is the application run in development
# cd ./src/
# python apps/app.py
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=settings.PORT_COMMANDLINE_APP, debug=True)
