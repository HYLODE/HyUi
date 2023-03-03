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
    discharged = pd.read_json(
        f"{get_settings().api_url}/hybye/discharge/n_days/{days}?campuses={campuses}"
    )
    admitted = pd.read_json(
        f"{get_settings().api_url}/hybye/admitted/n_days/{days}?campuses={campuses}"
    )

    df = pd.merge(
        discharged,
        admitted,
        on="event_date",
        suffixes=("_discharged", "_admitted"),
        how="left",
    )
    df = df.rename(
        columns={"count_discharged": "Discharged", "count_admitted": "Admitted"}
    )

    fig = ex.line(
        df,
        y=["Discharged", "Admitted"],
        x="event_date",
        labels={
            "value": "Number of Patients",
            "event_date": "Date",
        },
        title=f"{campuses} Discharges",
    )

    fig.update_layout(legend_title_text="Flow")

    return fig
