import dash
from dash import html

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks  # noqa

dash.register_page(__name__, path="/", name="Home")

timers = html.Div([])
stores = html.Div([])

body = html.Div([])


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
        ]
    )
