import json
import math
import requests
from dash import Input, Output, callback

from models.census import CensusRow
from web.config import get_settings
from web.pages.home import ids


@callback(
    Output(ids.CENSUS_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    background=True,
)
def _store_census(value: list[str] | str) -> list[dict]:
    if type(value) is str:
        campuses = [value]
    else:
        campuses = value  # type:ignore

    response = requests.get(
        f"{get_settings().api_url}/census/campus/", params={"campuses": campuses}
    )
    return [CensusRow.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(ids.CYTO_MAP, "layout"),
    Input(ids.LAYOUT_SELECTOR, "value"),
)
def _layout_control(val: str) -> dict:
    layouts = {
        "preset": {
            "name": "preset",
            "animate": True,
            "fit": True,
            "padding": 10,
        },
        "circle": {
            "name": "circle",
            "animate": True,
            "fit": True,
            "padding": 10,
            "startAngle": math.pi * 2 / 3,  # clockwise from 3 O'Clock
            "sweep": math.pi * 5 / 3,
        },
        "random": {
            "name": "random",
            "animate": True,
            "fit": True,
            "padding": 10,
        },
        "grid": {
            "name": "grid",
            "animate": True,
            "fit": True,
            "padding": 10,
            "cols": 5,
        },
    }
    return layouts.get(val, {})


@callback(
    Output(ids.CYTO_MAP, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    background=True,
)
def _prepare_cyto_elements(data: list[dict]) -> list[dict]:
    elements = list()
    for d in data:
        d = dict(
            id=d.get("location_string"),
            occupied=d.get("occupied", False),
        )
        element = dict(data=d)
        elements.append(element)
    return elements


@callback(
    Output(ids.DEBUG_NODE_INSPECTOR, "children"),
    Input(ids.CYTO_MAP, "tapNode"),
    prevent_initial_callback=True,
)
def tap_debug_inspector(data: dict) -> str:
    if data:
        data.pop("style", None)
    return json.dumps(data, indent=4)
