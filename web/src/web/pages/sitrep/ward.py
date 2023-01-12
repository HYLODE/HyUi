import dash
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, name="Ward", path="/ward")


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            dmc.Container(
                size="lg",
                mt=30,
                children=[dmc.Text("Here is the ward view " "for today")],
            )
        ]
    )
