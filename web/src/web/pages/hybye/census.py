import datetime
from typing import Tuple

import dash
import dash_mantine_components as dmc
from dash import html, dcc, Output, callback, Input
import pandas as pd
import plotly.express as ex

from web.config import get_settings

dash.register_page(__name__, path="/hybye/inpatients", name="Census")

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
        dmc.List(dmc.ListItem(id="summary_statistics")),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])


@callback(Output("los_plot", "figure"), Input("trigger", "n_clicks"))
def _return_los_plot(n_clicks) -> ex.histogram:
    df = pd.read_json(f"{get_settings().api_url}/hybye/census/uch")
    df = df[(df["occupied"]) & (df["patient_class"] == "INPATIENT")]
    df.ovl_admission = pd.to_datetime(df.ovl_admission, utc=True)
    # Handle extra ghost cases
    df = df[~df.location_string.str.contains("null")]
    df["los"] = datetime.datetime.now(tz=datetime.timezone.utc) - df.ovl_admission
    df["los"] = df.los.dt.days

    print(df.nlargest(5, "los"))
    print(df.los.std())

    fig = ex.histogram(df["los"], marginal="box")
    fig.update_xaxes(title_text="Length of Stay (Days)")

    return fig


@callback(Output("summary_statistics", "children"), Input("trigger", "n_clicks"))
def _return_los_summary_statistics(n_clicks) -> Tuple[str, str, str]:
    df = pd.read_json(f"{get_settings().api_url}/hybye/census/uch")
    df = df[(df["occupied"]) & (df["patient_class"] == "INPATIENT")]
    df.ovl_admission = pd.to_datetime(df.ovl_admission, utc=True)
    # Handle extra ghost cases
    df = df[~df.location_string.str.contains("null")]
    df["los"] = datetime.datetime.now(tz=datetime.timezone.utc) - df.ovl_admission
    df["los"] = df.los.dt.days

    return (
        f"Mean: {df.los.mean():.2f}\n",
        f"Median: {df.los.median().astype(int)}\n",
        f"Standard Deviation: {df.los.std():.2f}\n",
    )
