import json
import math
import requests
from dash import Input, Output, callback

from models.census import CensusRow
from web.config import get_settings
from web.pages.home import ids
from web.stores import ids as store_ids


@callback(Output(ids.DEPTS_OPEN_STORE, "data"), Input(store_ids.DEPT_STORE, "data"))
def _store_depts_open(depts: list[dict]) -> list[str]:
    """Return a list of open departments across all campuses"""
    return [
        d.get("department", "")
        for d in depts
        if not d.get("closed_temp") and not d.get("closed_perm")
    ]


@callback(
    Output(ids.CENSUS_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    background=True,
)
def _store_census(value: list[str] | str, depts_open: list[str]) -> list[dict]:
    """
    Store CensusRow as list of dictionaries after filtering out closed
    departments for that building
    Args:
        value: one of UCH/WMS/GWB/NHNN
        depts_open: list of departments that are open

    Returns:
        Filtered list of CensusRow dictionaries

    """
    if type(value) is str:
        campuses = [value]
    else:
        campuses = value  # type:ignore

    response = requests.get(
        f"{get_settings().api_url}/census/campus/", params={"campuses": campuses}
    )

    res = [CensusRow.parse_obj(row).dict() for row in response.json()]
    res = [row for row in res if row.get("department") in depts_open]
    return res


@callback(
    (
        Output(ids.ROOM_SET_STORE, "data"),
        Output(ids.DEPT_SET_STORE, "data"),
    ),
    Input(ids.CENSUS_STORE, "data"),
)
def _store_dept_and_room_sets(data: list[dict]) -> tuple[list[str], list[str]]:
    """
    Return a list unique rooms
    To be safe we use the pairing of the room and the ward to define uniqueness
    """
    locations = [i.get("location_string", "^^") for i in data]
    rooms = ["^".join(i.split("^")[:2]) for i in locations]
    depts = ["^".join(i.split("^")[:1]) for i in locations]
    return list(set(rooms)), list(set(depts))


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
            # "cols": 5,
        },
    }
    return layouts.get(val, {})


@callback(
    Output(ids.CYTO_MAP, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    Input(ids.ROOM_SET_STORE, "data"),
    Input(ids.DEPT_SET_STORE, "data"),
    background=True,
)
def _prepare_cyto_elements(
    census: list[dict],
    rooms: list[str],
    depts: list[str],
) -> list[dict]:
    elements = list()

    for bed in census:
        location_string = bed.get("location_string")
        if not location_string:
            continue

        data = dict(
            id=location_string,
            occupied=bed.get("occupied", False),
            parent="^".join(location_string.split("^")[:2]),
            entity="bed",
        )

        elements.append(dict(data=data))

    for room in rooms:
        dept = room.split("^")[0]
        data = dict(
            id=room,
            parent=dept,
            entity="room",
        )
        elements.append(dict(data=data))

    for dept in depts:
        data = dict(id=dept, entity="department")
        elements.append(dict(data=data))

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
