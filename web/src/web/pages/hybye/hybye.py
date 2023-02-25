import dash
import dash_mantine_components as dmc
from dash import html

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
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
                        )
                    ]
                ),
            ]
        )
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])
