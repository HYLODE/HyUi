# Run this app with `python app.py` and
# visit http://127.0.0.1:8095/ in your web browser.

import pandas as pd
import plotly.express as px
import requests

from dash import Dash, html, dcc, Input, Output
from dash import dash_table as dt

from config.settings import settings
from utils import df_from_url

REFRESH_INTERVAL = 5*60*1000 # milliseconds
API_URL = settings.BACKEND_URL
app = Dash(__name__)



@app.callback(
    Output("fig_consults", "children"),
    Input("query-interval", "n_intervals"),
    )
def consults_over_time(n_intervals):
    df = df_from_url(API_URL)

    df = df.groupby("name").resample("60T", on="scheduled_datetime").agg({"dept_name": "size"})
    df.reset_index(inplace=True)
    fig = px.bar(df, x="scheduled_datetime", y="dept_name", color="name")

    return dcc.Graph(figure=fig)



# basic_table = html.Div(
#     [
#         html.P("Printing a simple table from the API"),
#         dt.DataTable(
#             id="api_table",
#             columns=[{"name": i, "id": i} for i in df.columns],
#             data=df.to_json(orient="records"),
#             filter_action="native",
#             sort_action="native",
#         ),
#     ]
# )


dash_only = html.Div(
    dcc.Interval(id="query-interval", interval=REFRESH_INTERVAL, n_intervals=0)
)



app.layout = html.Div(
    children=[
        html.Div(id="fig_consults"),
        dash_only,
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8095)
