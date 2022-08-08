# src/apps/pages/hymind/hymind.py
"""
Sub-application for HyMind
"""

import arrow
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html, register_page
from pydantic import parse_obj_as

from apps.pages.hymind import BPID, HYMIND_ENV, REFRESH_INTERVAL, wng
from config.settings import settings
from utils import get_model_from_route
from utils.dash import df_from_store, get_results_response

register_page(__name__)

em_tap_model = get_model_from_route("HyMind", standalone="EmTap")
em_tap_url = wng.build_emergency_tap_url()

main_layout = html.Div([html.P("Hello")])

dash_only = html.Div(
    [
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        em_tap_data := dcc.Store(id=f"{BPID}em_tap_data"),
    ]
)

layout = html.Div(
    [
        main_layout,
        dash_only,
    ]
)


@callback(
    Output(em_tap_data, "data"),
    Input(query_interval, "n_intervals"),
    # Input(f"{BPID}building_radio", "value"),
)
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
