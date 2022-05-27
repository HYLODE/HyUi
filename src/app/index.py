# Run this app with `python app.py` and
# visit http://127.0.0.1:8095/ in your web browser.

import pandas as pd
import plotly.express as px
import requests

from dash import Dash, html, dcc
from dash import dash_table as dt

from config.settings import settings
from utils import df_from_url

API_URL = settings.BACKEND_URL



def consults_over_time(df):
    df = df[["scheduled_datetime", "dept_name"]]
    df.set_index("scheduled_datetime", inplace=True)
    df = df.resample("30T").agg({"dept_name": "size"})
    fig = px.bar(df, x=df.index, y="dept_name")
    return fig


df = df_from_url(API_URL)

basic_table = html.Div(
    [
        html.P("Printing a simple table from the API"),
        dt.DataTable(
            id="api_table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_json(orient="records"),
            filter_action="native",
            sort_action="native",
        ),
    ]
)


fig = consults_over_time(df)


app = Dash(__name__)

app.layout = html.Div(
    children=[
        # basic_table
        dcc.Graph(figure=fig)
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8095)
