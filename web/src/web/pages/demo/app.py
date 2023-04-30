import dash
import dash_mantine_components as dmc
import orjson
import requests
from dash import Input, Output

from web import campus_url
from web.celery import redis_client
from web.celery_tasks import get_response
from web.pages.demo import fast_url, slow_url
from web.style import colors

dash.register_page(__name__, path="/demo", name="demo")


@dash.callback(
    Output("ping-fast-text", "children"),
    [Input("ping-fast-button", "n_clicks")],
    prevent_initial_call=True,
)
def ping_fast(n_clicks):
    response = requests.get(fast_url)
    data = response.json()
    return f"Click: {n_clicks} Timestamp: {data}"


@dash.callback(
    Output("ping-slow-text", "children"),
    [Input("ping-slow-button", "n_clicks")],
    prevent_initial_call=True,
)
def ping_slow(n_clicks):
    # check the redis cache for the data
    cache_key = "slow_url"
    cached_data = redis_client.get(cache_key)

    if cached_data is None:
        fetch_data_task = get_response.delay(slow_url, cache_key)
        data = fetch_data_task.get()
    else:
        data = orjson.loads(cached_data)

    return f"Click: {n_clicks} Timestamp: {data}"


@dash.callback(
    Output("ping-campus-text", "children"),
    [Input("ping-campus-button", "n_clicks")],
    prevent_initial_call=True,
)
def ping_campus(n_clicks):
    cache_key = "campus_url"
    cached_data = redis_client.get(cache_key)
    if cached_data is None:
        fetch_data_task = get_response.delay(campus_url, cache_key)
        data = fetch_data_task.get()
    else:
        data = orjson.loads(cached_data)

    result = len(data)
    return f"Click: {n_clicks} Rows of data: {result}"


layout = dmc.Paper(
    [
        dmc.Title("Hello World"),
        dmc.Group(
            [
                dmc.Button(id="ping-fast-button", children="Ping-fast"),
                dmc.Text(id="ping-fast-text"),
            ],
            p=10,
        ),
        dmc.Group(
            [
                dmc.Button(id="ping-slow-button", children="Ping-slow"),
                dmc.Text(id="ping-slow-text"),
            ],
            p=10,
        ),
        dmc.Group(
            [
                dmc.Button(id="ping-campus-button", children="Ping-campus"),
                dmc.Text(id="ping-campus-text"),
            ],
            p=10,
        ),
    ]
)
