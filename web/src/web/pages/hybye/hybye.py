import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

import web.pages.sitrep.callbacks.cytoscape  # noqa

dash.register_page(__name__, path="/hybye/stage", name="HyBye")

body = html.Div(
    [
        dmc.Paper(
            [
                dmc.Text(
                    dmc.Title("HyBye: Patient Discharge Prediction Modelling ⚙️"),
                    variant="gradient",
                    gradient={"from": "red", "to": "yellow", "deg": 45},
                ),
                dmc.Divider(),
                dmc.Container(
                    [
                        dmc.Text(
                            "This is a work in progress for the discharge prediction model.",
                            style={"padding-top": "2rem", "fontSize": 20},
                        ),
                        dmc.Divider(style={"padding-top": "2rem"}),
                        dmc.List(
                            [
                                dmc.ListItem(
                                    dmc.Anchor(
                                        dmc.Group(
                                            [
                                                dmc.Text(
                                                    "Discharge Overview: Patient flow indicators",
                                                    style={
                                                        "padding-top": "2rem",
                                                        "fontSize": 20,
                                                    },
                                                ),
                                                dmc.Button(
                                                    "Open Flow Dashboard",
                                                    leftIcon=DashIconify(
                                                        icon="mdi:clipboard-flow"
                                                    ),
                                                ),
                                            ]
                                        ),
                                        href="/hybye/flow",
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ]
        )
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])
