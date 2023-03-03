from dash import callback, Output, Input
import pandas as pd
import plotly.express as ex

from web.config import get_settings


@callback(Output("discharge_flow", "figure"), Input("input_days", "value"))
def _get_discharge_flow(days: int = 7) -> ex.line:
    url = f"{get_settings().api_url}/hybye/discharge/n_days/{days}"
    print(url)
    df = pd.read_json(url)
    fig = ex.line(
        y=df["count"],
        x=df["discharge_date"],
        labels={
            "y": "Patients Discharged",
            "x": "Date",
        },
    )

    return fig
