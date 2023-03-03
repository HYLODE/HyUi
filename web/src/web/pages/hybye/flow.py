import dash
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from web.pages.hybye.callbacks import flow  # noqa

dash.register_page(__name__, path="/hybye/flow", name="Hospital Flow")

body = html.Div(
    [
        html.H2("Discharge Flow Dashboard"),
        dcc.Graph(id="discharge_flow"),
        dmc.NumberInput(
            id="input_days",
            label="Days",
            description="Days to graph back",
            value=14,
            min=2,
            debounce=1,
            stepHoldDelay=500,
            stepHoldInterval=100,
            step=7,
            icon=DashIconify(icon="material-symbols:calendar-month"),
            style={"width": 200, "margin-left": 100},
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])
