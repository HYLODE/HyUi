"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import requests
from dash import Input, Output, callback, dcc, html

from models.beds import Bed, Department, Room
from web import ids
from web.config import get_settings
from web.utils import Timer


# TODO: add a refresh button as an input to the store functions pulling from
#  baserow so that changes from baserow edits can be brought through (
#  although a page refresh may do the same thing?)


@callback(
    Output(ids.DEPT_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@Timer(text="App department store: Elapsed time: {:.3f} seconds")
def _store_departments(_: int) -> list[dict]:
    """Store all open departments"""
    response = requests.get(
        f"{get_settings().api_url}/baserow/departments/",
    )
    depts = [Department.parse_obj(row).dict() for row in response.json()]
    return [d for d in depts if not d.get("closed_perm_01")]


@callback(
    Output(ids.ROOM_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@Timer(text="App room store: Elapsed time: {:.3f} seconds")
def _store_rooms(_: int) -> list[dict]:
    """Store all rooms with beds"""
    response = requests.get(
        f"{get_settings().api_url}/baserow/rooms/",
    )
    rooms = [Room.parse_obj(row).dict() for row in response.json()]
    return [r for r in rooms if r.get("has_beds")]


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@Timer(text="App bed store: Elapsed time: {:.3f} seconds")
def _store_beds(_: int) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/baserow/beds/",
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


stores = html.Div(
    [
        dcc.Store(id=ids.DEPT_STORE),
        dcc.Store(id=ids.ROOM_STORE),
        dcc.Store(id=ids.BEDS_STORE),
    ]
)
