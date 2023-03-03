from dash import callback, Output, Input
import pandas as pd
import plotly.express as ex

from web.config import get_settings


@callback(
    Output("discharge_flow", "figure"),
    Input("input_days", "value"),
    Input("campus_select", "value"),
)
def _get_discharge_flow(days: int = 7, campuses: str = "UCH") -> ex.line:
    url = f"{get_settings().api_url}/hybye/discharge/n_days/{days}?campuses={campuses}"
    df = pd.read_json(url)
    fig = ex.line(
        y=df["count"],
        x=df["event_date"],
        labels={
            "y": "Patients Discharged",
            "x": "Date",
        },
        title=f"{campuses} Discharges",
    )

    return fig
