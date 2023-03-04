import dash
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from web.pages.hybye.callbacks import flow  # noqa

dash.register_page(
    __name__,
    path="/hybye/flow",
    name="Hospital Flow",
    external_stylesheets="./flow.css",
)

CAMPUSES = ["UCH", "WMS", "GWB", "NHNN"]
input_style = {"width": 200, "margin-left": 100}
icon_style = {"margin-left": 18, "color": "rgb(173, 181, 189)"}

body = html.Div(
    [
        html.H1(
            children=[
                "Hospital Flow Dashboard",
                DashIconify(icon="mdi:clipboard-flow", style={"padding-top": "0.5rem"}),
            ]
        ),
        dmc.LoadingOverlay(children=dcc.Graph(id="discharge_flow")),
        dmc.SimpleGrid(
            cols=2,
            children=[
                dmc.Select(
                    label="Select Site",
                    description="Site to view discharges from",
                    id="campus_select",
                    value="UCH",
                    data=[{"value": campus, "label": campus} for campus in CAMPUSES],
                    icon=DashIconify(icon="material-symbols:local-hospital"),
                    style=input_style,
                ),
                dmc.Group(
                    [
                        DashIconify(icon="mdi:scale-balance", style=icon_style),
                        html.Div(id="patient_net"),
                    ],
                    style={"align-content": "end"},
                ),
                dmc.NumberInput(
                    id="input_days",
                    label="Timeframe",
                    description="Days to graph back",
                    value=14,
                    min=7,
                    debounce=500,
                    stepHoldDelay=500,
                    stepHoldInterval=100,
                    step=7,
                    icon=DashIconify(icon="material-symbols:calendar-month"),
                    style=input_style,
                ),
                dmc.Group(
                    [
                        DashIconify(icon="tabler:math-avg", style=icon_style),
                        html.Div(id="flow_average"),
                    ],
                    style={"align-content": "end"},
                ),
            ],
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])
