import dash
import dash_mantine_components as dmc
from dash import html, dash_table
from dash_iconify import DashIconify
import pandas as pd

from web.config import get_settings

dash.register_page(__name__, path="/hybye/inpatients", name="Census")

df = pd.read_json(f"{get_settings().api_url}/hybye/census/uch")
df = df[(df["occupied"]) & (df["patient_class"] == "INPATIENT")]

# print(df.head())

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
        html.H1(
            children=[
                "UCH Inpatient State",
                DashIconify(
                    icon="material-symbols:inpatient-rounded",
                    style={"padding-top": "0.5rem"},
                ),
            ]
        ),
        dash_table.DataTable(
            df.to_dict("records"),
            columns=[{"id": col, "name": col} for col in cols_select],
        ),
    ]
)


def layout() -> dash.html.Div:
    return html.Div(children=[body])
