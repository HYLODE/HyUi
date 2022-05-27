# Run this app with `python app.py` and
# visit http://127.0.0.1:8095/ in your web browser.

import pandas as pd
import plotly.express as px
import requests

from dash import Dash, html, dcc, Input, Output, State
from dash import dash_table as dt

from config.settings import settings
from utils import get_results_response, df_from_store

REFRESH_INTERVAL = 5*60*1000 # milliseconds
API_URL = settings.BACKEND_URL
app = Dash(__name__)


@app.callback(
    Output("request_data", "data"),
    Input("query-interval", "n_intervals"),
    )
def store_data(n_intervals: int) -> dict:
    """
    Read data from API then store as JSON
    """
    data = get_results_response(API_URL)
    return data


@app.callback(
    Output("fig_consults", "children"),
    Input("request_data", "modified_timestamp"),
    State("request_data", "data"),
    prevent_initial_call=True,
    )
def gen_consults_over_time(n_intervals: int, data: dict):
    """
    Plot stacked bar
    """
    df = df_from_store(data)
    df = df.groupby("name").resample("60T", on="scheduled_datetime").agg({"dept_name": "size"})
    df.reset_index(inplace=True)
    fig = px.bar(df, x="scheduled_datetime", y="dept_name", color="name")
    return dcc.Graph(figure=fig)



@app.callback(
    Output("table_consults", "children"),
    Input("request_data", "modified_timestamp"),
    State("request_data", "data"),
    prevent_initial_call=True,
    )
def gen_table_consults(n_intervals: int, data: dict):
    cols = dict(
        firstname="First name",
        lastname="Last name",
        date_of_birth="DoB",
        mrn="MRN",
        name="Consult",
        scheduled_datetime="Consult time",
    )
    return [
        dt.DataTable(
            id="results_table",
            columns=[{"name": v, "id": k} for k,v in cols.items()],
            data=data,
            filter_action="native",
            sort_action="native", )
    ]


dash_only = html.Div([
    dcc.Interval(id="query-interval", interval=REFRESH_INTERVAL, n_intervals=0),
    dcc.Store(id="request_data"),
])



app.layout = html.Div(
    children=[
        html.Div(id="fig_consults"),
        html.Div(id="table_consults"),
        dash_only,
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8095)
