import datetime

import dash
import dash_mantine_components as dmc
from dash import html, dash_table, dcc, Output, callback, Input
from dash_iconify import DashIconify
import pandas as pd
import plotly.express as ex

from web.config import get_settings

dash.register_page(__name__, path="/hybye/inpatients", name="Census")

df = pd.read_json(f"{get_settings().api_url}/hybye/census/uch")
df = df[(df["occupied"]) & (df["patient_class"] == "INPATIENT")]

cols_select = [
    "department",
    "location_string",
    "ovl_admission",
    "open_visits_n",
    "ovl_ghost",
    "occupied",
    "patient_class",
    "mrn",
    "lastname",
    "firstname",
    "date_of_birth",
]

body = html.Div(
    [
        html.H1("UCH Inpatient State"),
        dcc.Graph("los_plot"),
        dmc.Button("Render Results", id="trigger"),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])


@callback(Output("los_plot", "figure"), Input("trigger", "n_clicks"))
def _return_los_plot(n_clicks):
    df.ovl_admission = pd.to_datetime(df.ovl_admission, utc=True)
    df["los"] = datetime.datetime.now(tz=datetime.timezone.utc) - df.ovl_admission
    df["los"] = df.los.dt.days

    print(df.los)

    return ex.histogram(df["los"], marginal="box")
