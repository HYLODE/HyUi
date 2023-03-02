import dash
from dash import html, dcc, callback, Output, Input
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import requests
import plotly.express as ex

from web.config import get_settings

dash.register_page(__name__, path="/hybye/flow", name="Hospital Flow")

body = html.Div(
    [
        dcc.Graph(id="discharge_flow"),
        # dcc.Input(id="input_days", type="number", placeholder="Days", value="14", debounce=True)
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
            style={"width": 200, "margin-left": 100}
        ),
    ]
)


@callback(Output("discharge_flow", "figure"), Input("input_days", "value"))
def _get_discharge_flow(days=7):
    url = f"{get_settings().api_url}/hybye/discharge/n_days/{days}"
    print(url)
    df = pd.read_json(url)
    fig = ex.line(
        y=df["count"],
        x=df["discharge_date"],
        labels={
            "y": "Count Discharged",
            "x": "Date",
        },
        title="Discharge Flow",
    )

    return fig


def layout() -> dash.html.Div:
    return html.Div(children=[body])
