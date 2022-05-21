# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import plotly.express as px
import requests

from dash import Dash, html, dcc
from dash import dash_table as dt

from config.settings import settings

API_URL = settings.BACKEND_URL


def request_data(url: str) -> list:
    """
    requests.json() should return a list of dicts
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # raises HTTP errors
    except requests.exceptions.HTTPError as e:
        print("!!! HTTP Error", e)
    except requests.exceptions.RequestException as e:
        print("!!! Catch-all Error", e)

    try:
        assert response.headers["Content-Type"] == "application/json"
    except:
        raise ValueError("response is not JSON")
    return response.json()


def consults_over_time(data):
    df = pd.DataFrame.from_records(data)
    df["scheduled_datetime"] = pd.to_datetime(
        df["scheduled_datetime"], infer_datetime_format=True
    )
    df = df[["scheduled_datetime", "dept_name"]]
    df.set_index("scheduled_datetime", inplace=True)
    df = df.resample("30T").agg({"dept_name": "size"})

    fig = px.bar(df, x=df.index, y="dept_name")
    # fig = px.line(df, x=df.index, y="dept_name")
    return fig


api_json = request_data(API_URL)

basic_table = html.Div(
    [
        html.P("Printing a simple table from the API"),
        dt.DataTable(
            id="api_table",
            columns=[{"name": i, "id": i} for i in api_json[0].keys()],
            data=api_json,
            filter_action="native",
            sort_action="native",
        ),
    ]
)


fig = consults_over_time(api_json)


app = Dash(__name__)

app.layout = html.Div(
    children=[
        # basic_table
        dcc.Graph(figure=fig)
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8095)
