"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import requests
from dash import Input, Output, callback, dcc, html

from models.census import CensusDepartment
from web import ids
from web.config import get_settings


@callback(
    Output(ids.DEPT_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    # background=True,
)
def _store_departments(_: int) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/census/departments/",
    )
    return [CensusDepartment.parse_obj(row).dict() for row in response.json()]


stores = html.Div(
    [
        dcc.Store(id=ids.DEPT_STORE),
    ]
)
