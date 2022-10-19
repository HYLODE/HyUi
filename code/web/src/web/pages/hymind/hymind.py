import arrow
import plotly.graph_objects as go
import requests
from dash import Input, Output, callback, dcc, get_app, register_page
from flask_caching import Cache

from models.hymind import EmTap, ElTap
from web.pages.hymind import (
    BPID,
    CACHE_TIMEOUT,
    layout,
    wng,
)
from utils.dash import df_from_store, get_results_response

register_page(__name__)
app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)

em_tap_url = wng.build_emergency_tap_url()

el_tap_url = wng.build_elective_tap_url()

layout = layout.layout()


@callback(
    Output(f"{BPID}em_tap_data", "data"),
    Input(f"{BPID}query_interval", "n_intervals"),
    # Input(f"{BPID}building_radio", "value"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_em_tap(n_intervals: int, building: str = "tower"):
    """
    { item_description }
    """
    building = building.lower()
    assert building in ["tower", "gwb", "wms"]
    payload = dict(
        horizon_dt=arrow.now().shift(days=1).format("YYYY-MM-DDTHH:mm:ss"),
        department=building,
    )
    # import ipdb; ipdb.set_trace()
    predictions = get_results_response(em_tap_url, "POST", json=payload)
    return predictions


@callback(
    Output(f"{BPID}em_tap_fig", "children"),
    Input(f"{BPID}em_tap_data", "data"),
    prevent_initial_callback=True,
)
def em_tap_fig(data: dict):

    # TODO: Figure out why an empty dictionary is being returned.
    if len(data) == 1 and not data[0]:
        return None

    df = df_from_store(data, EmTap)
    # fig = px.bar(df, x="bed_count", y="probability")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["bed_count"],
            y=1 - df["probability"].cumsum(),
            offset=0.5,
        )
    )
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(template="plotly_white")
    config = {
        "displayModeBar": False,
        "staticPlot": True,
        "autosizable": True,
    }
    return dcc.Graph(id="em_tap_fig_graph", figure=fig, config=config)


@callback(
    Output(f"{BPID}el_tap_data", "data"),
    Input(f"{BPID}query_interval", "n_intervals"),
    # Input(f"{BPID}building_radio", "value"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_el_tap(n_intervals: int, building: str = "tower"):
    building = building.lower()
    assert building in ["tower", "gwb", "wms"]

    # import ipdb; ipdb.set_trace()
    resp = requests.get(
        el_tap_url,
        params={
            "horizon_dt": arrow.now().shift(days=1).format("YYYY-MM-DDTHH:mm:ss"),
            "department": building,
        },
    )
    # predictions = get_results_response(el_tap_url, "POST", json=payload)
    return resp


@callback(
    Output(f"{BPID}el_tap_fig", "children"),
    Input(f"{BPID}el_tap_data", "data"),
    prevent_initial_callback=True,
)
def el_tap_fig(data: dict):

    # TODO: Figure out why an empty dictionary is being returned.
    if len(data) == 1 and not data[0]:
        return None

    df = df_from_store(data, ElTap)
    # fig = px.bar(df, x="bed_count", y="probability")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["bed_count"],
            y=1 - df["probability"].cumsum(),
            offset=0.5,
        )
    )
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(template="plotly_white")
    config = {
        "displayModeBar": False,
        "staticPlot": True,
        "autosizable": True,
    }
    return dcc.Graph(id="el_tap_fig_graph", figure=fig, config=config)
