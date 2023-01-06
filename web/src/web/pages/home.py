import dash
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, path="/", name="Home")


def layout() -> dash.html.Div:
    return html.Div(
        children=[dmc.Container(size="lg", mt=30, children=[dmc.Text("Hello world")])]
    )
