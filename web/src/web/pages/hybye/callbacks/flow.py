from dash import callback, Output, Input
import pandas as pd
import plotly.express as ex

from web.config import get_settings


@callback(
    Output("discharge_flow", "figure"),
    Output("patient_net", "children"),
    Output("flow_average", "children"),
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

    figure = ex.line(
        df,
        y=["Discharged", "Admitted"],
        x="event_date",
        labels={
            "value": "Number of Patients",
            "event_date": "Date",
        },
        title=f"{campuses} Flow",
    )

    figure.update_layout(legend_title_text="Flow")

    patient_net = df["Admitted"] - df["Discharged"]
    patient_net = f"Timeframe Net Balance: {patient_net.sum(axis=0)}"

    flow_average = df.mean(axis=0, numeric_only=True)
    flow_average = (
        f"Admitted: {flow_average[0]:.2f} → Discharged: {flow_average[1]:.2f}"
    )

    return figure, patient_net, flow_average
