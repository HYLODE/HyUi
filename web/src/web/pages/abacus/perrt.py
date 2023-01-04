"""
Module to manage the display of patient details on the page
"""
import dash
import dash_bootstrap_components as dbc
import requests
import pandas as pd

# import plotly.graph_objs as go
import plotly.express as px

from dash import Input, Output, callback, dcc, html

from models.perrt import EmapVitalsLong
from web.config import get_settings
from web.convert import parse_to_data_frame
from . import BPID
from web.pages.abacus.map import input_tapnode, input_encounter

store_perrt_long = dcc.Store(id=f"{BPID}perrt_long")
input_perrt_long = Input(f"{BPID}perrt_long", "data")


@callback(
    Output(f"{BPID}perrt_long", "data"),
    input_encounter,
    prevent_initial_call=True,
)
def _store_patient_details(encounter: int, hours: int = 24) -> list[dict]:
    """Run PERRT vitals long query and return to store"""
    if encounter:
        response = requests.get(
            url=f"{get_settings().api_url}/perrt/vitals/long",
            params={"encounter_ids": [encounter], "horizon_dt": hours},
        )
        return [EmapVitalsLong.parse_obj(row).dict() for row in response.json()]
    else:
        return [{}]


card_details = html.Div(
    id=f"{BPID}details_card_div",
    children=dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(id=f"{BPID}perrt_plot"),
                ]
            ),
        ]
    ),
)


@callback(
    Output(f"{BPID}details_card_div", "hidden"),
    input_tapnode,
    Input(f"{BPID}perrt_long", "data"),
    prevent_initial_callback=True,
)
def _set_details_card_div_hidden(node: dict, perrt: dict):
    """set the hidden property of the details_card_visible div"""
    if not node:
        return True
    if node.get("data").get("occupied") is False:
        return True
    if perrt is None or not any(perrt):
        return True
    return False


@callback(
    Output(f"{BPID}perrt_plot", "children"),
    Input(f"{BPID}perrt_long", "data"),
    prevent_initial_callback=True,
)
def _plot_perrt(perrt):
    """ """
    if not perrt or not any(perrt):
        return dash.no_update

    df = parse_to_data_frame(perrt, EmapVitalsLong)
    df_hr = df[df["id_in_application"] == "8"]
    df_hr.sort_values(by="observation_datetime", inplace=True)
    fig = px.line(df_hr, x="observation_datetime", y="value_as_real")
    # plotly express returns a plotly.go object so use same approach to
    # modifying
    fig.update_layout(
        title="Recent heart rate",
        xaxis_title="Date/Time",
        yaxis_title="Heart rate",
    )

    return dcc.Graph(figure=fig)
