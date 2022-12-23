import json
import math

from dash import Input, Output, callback, dcc
from web.hospital import get_building_departments

# callback functions created here will be labelled with BPID for abacus
from web.pages.abacus import BPID
from web.pages.abacus.utils import (
    _get_beds,
    _get_census,
    _get_sitrep_status,
    _make_bed,
    _populate_beds,
    _list_of_unique_rooms,
    _make_room,
    _present_patient,
)


@callback(
    Output(f"{BPID}departments", "data"), Input(f"{BPID}query_interval", "n_intervals")
)
def get_all_departments(n_intervals: int):
    building_departments = get_building_departments()
    return [bd.dict() for bd in building_departments]


@callback(
    Output(f"{BPID}dept_dropdown_div", "children"),
    Input(f"{BPID}building_radio", "value"),
    Input(f"{BPID}departments", "data"),
)
def gen_dept_dropdown(building: str, building_departments):
    """
    Dynamically build department picker list
    """

    dropdown: list[str] = []
    for bd in building_departments:
        if bd["building"] == building:
            dropdown.extend(bd.get("departments"))
            break

    return dcc.Dropdown(
        id=f"{BPID}dept_dropdown",
        value=dropdown[0],
        options=[{"label": v, "value": v} for v in dropdown],
        placeholder="Pick a department",
        multi=False,
    )


@callback(
    Output(f"{BPID}beds", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
)
def get_beds(department: str) -> list[dict]:
    beds = _get_beds(department=department)
    return beds


@callback(
    Output(f"{BPID}census", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
)
def get_census(department: str) -> list[dict]:
    census = _get_census(department=department)
    return census


@callback(
    Output(f"{BPID}sitrep", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
)
def get_sitrep(department: str) -> list[dict]:
    return _get_sitrep_status(department=department)


@callback(
    Output(f"{BPID}bed_map", "layout"),
    Input(f"{BPID}layout_radio", "value"),
)
def update_layout(layout: str) -> dict:
    layouts = {
        "preset": {"name": "preset", "fit": True, "padding": 80},
        "random": {"name": "random", "animate": True},
        "circle": {
            "name": "circle",
            "fit": True,
            "padding": 10,
            "startAngle": math.pi * 2 / 3,  # clockwise from 3 O'Clock
            "sweep": math.pi * 5 / 3,
            "animate": True,
        },
        "grid": {"name": "grid", "cols": 5, "fit": True, "animate": True},
    }
    return layouts.get(layout, "circle")


@callback(
    Output(f"{BPID}bed_map", "elements"),
    Input(f"{BPID}census", "data"),
    Input(f"{BPID}beds", "data"),
    Input(f"{BPID}layout_radio", "value"),
    prevent_initial_call=True,
)
def store_patients_in_beds(census, beds, layout):
    preset = True if layout == "preset" else False
    bed_list = [_make_bed(i, preset) for i in beds]
    bed_list.sort(key=lambda bed: bed.get("data").get("bed_index"))

    patient_list = _populate_beds(bed_list, census)
    room_list = [_make_room(r, preset) for r in _list_of_unique_rooms(beds)]

    nodes = patient_list + room_list

    edges = []

    return nodes + edges


@callback(
    Output(f"{BPID}bed_inspector", "children"),
    Input(f"{BPID}bed_map", "tapNode"),
    prevent_initial_callback=True,
)
def tap_bed_inspector(data):
    if data:
        return _present_patient(data.get("data").get("census"))
    else:
        return ""


@callback(
    Output(f"{BPID}node_inspector", "children"),
    Input(f"{BPID}bed_map", "tapNode"),
    prevent_initial_callback=True,
)
def tap_node_inspector(data):
    return json.dumps(data, indent=4)
