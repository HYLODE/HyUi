import json
import math
import warnings
from dash import Input, Output, State, callback, ctx, dcc

from web.hospital import get_building_departments

# callback functions created here will be labelled with BPID for abacus
from web.pages.abacus import BPID
from web.pages.abacus.utils import (
    _get_beds,
    _get_census,
    _get_perrt_long,
    _get_sitrep_status,
    _list_of_unique_rooms,
    _make_bed,
    _make_room,
    _populate_beds,
    _present_patient,
    _update_patients_with_sitrep,
    _post_discharge_status,
)
from . import SITREP_DEPT2WARD_MAPPING


@callback(
    Output(f"{BPID}departments", "data"),
    Input(f"{BPID}page_interval", "n_intervals"),
    background=True,
)
def store_all_departments(n_intervals: int):
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
    background=True,
)
def store_beds(department: str) -> list[dict]:
    beds = _get_beds(department=department)
    return beds


@callback(
    Output(f"{BPID}census", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
    background=True,
)
def store_census(department: str) -> list[dict]:
    census = _get_census(department=department)
    return census


@callback(
    Output(f"{BPID}sitrep", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_callback=True,
    background=True,
)
def store_sitrep(department: str) -> list[dict]:
    """
    Use census to provide the CSNs that can be used to query additional data
    Args:
        department: the department

    Returns:
        additonal patient level data

    """

    if department in SITREP_DEPT2WARD_MAPPING.keys():
        # simulate delay in API request
        # import time
        # time.sleep(3)

        return _get_sitrep_status(department=department)
    else:
        warnings.warn(f"No sitrep data available for {department}")
        return [{}]


@callback(
    Output(f"{BPID}tap_node", "data"),
    Input(f"{BPID}bed_map", "tapNode"),
    Input(f"{BPID}dept_dropdown", "value"),
    Input(f"{BPID}building_radio", "value"),
    prevent_initial_call=True,
)
def store_tap_node(data: list[dict], dept: str, bldg: str) -> list[dict]:
    if ctx.triggered_id == f"{BPID}bed_map":
        return data
    else:
        return [{}]


@callback(
    Output(f"{BPID}patient_details", "data"),
    Input(f"{BPID}bed_map", "tapNode"),
    prevent_initial_call=True,
)
def store_patient_details(element: dict) -> list[dict]:
    """Run PERRT vitals long query and return to store"""
    if not element.get("data").get("occupied"):
        return [{}]
    else:
        encounter = element.get("data").get("encounter", None)
        return _get_perrt_long(encounter, hours=6)


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
    return layouts.get(layout)


@callback(
    Output(f"{BPID}bed_map", "elements"),
    Input(f"{BPID}census", "data"),
    Input(f"{BPID}beds", "data"),
    Input(f"{BPID}sitrep", "data"),
    Input(f"{BPID}layout_radio", "value"),
    prevent_initial_call=True,
)
def make_cytoscape_elements(census, beds, sitrep, layout):
    preset = True if layout == "preset" else False

    room_list = [_make_room(r, preset) for r in _list_of_unique_rooms(beds)]

    bed_list = [_make_bed(i, preset) for i in beds]
    bed_list.sort(key=lambda bed: bed.get("data").get("bed_index"))

    bed_list = _populate_beds(bed_list, census)
    if sitrep and sum([len(i) for i in sitrep]):
        bed_list = _update_patients_with_sitrep(bed_list, sitrep)

    nodes = bed_list + room_list
    edges = []
    elements = nodes + edges
    # Update elements so that none selected on first instantiation I think this
    # works b/c elements is a mutable list so we are actually modifying its
    # contents
    for ele in elements:
        ele["selected"] = False

    return elements


@callback(
    Output(f"{BPID}bed_inspector", "children"),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_callback=True,
)
def tap_bed_inspector(data: dict):
    if data and any(data):
        return _present_patient(
            census=data.get("data").get("census"),
            sitrep=data.get("data").get("sitrep"),
        )
    else:
        return ""


@callback(
    Output(f"{BPID}patient_inspector", "children"),
    Input(f"{BPID}patient_details", "data"),
    prevent_initial_callback=True,
)
def patient_inspector(data: list[dict]):
    if data and any(data):
        return json.dumps(data, indent=4)
    else:
        return ""


@callback(
    Output(f"{BPID}node_inspector", "hidden"),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_callback=True,
)
def tap_node_inspector(data: dict):
    """set the hidden property of the node_inspector div"""
    visible = False  # easier than double negative hidden
    if data and any(data):
        return visible if data.get("data").get("occupied") else not visible
    else:
        return not visible


@callback(
    Output(f"{BPID}discharge_radio", "value"),
    Input(f"{BPID}tap_node", "data"),
    State(f"{BPID}discharge_update", "data"),
    prevent_initial_call=True,
)
def set_discharge_status(node: dict, discharge_update: dict):
    """sets discharge status"""
    discharge_status = "no"

    if not node or not all(node):
        return discharge_status
    else:
        encounter = node.get("data").get("encounter")

    if discharge_update:
        discharge_status = discharge_update.get(encounter, discharge_status)

    return discharge_status


@callback(
    (
        Output(f"{BPID}discharge_update", "data"),
        Output(f"{BPID}discharge_submit_button", "disabled"),
        Output(f"{BPID}discharge_submit_button", "color"),
    ),
    Input(f"{BPID}discharge_submit_button", "n_clicks"),
    Input(f"{BPID}discharge_radio", "value"),
    Input(f"{BPID}tap_node", "data"),
    State(f"{BPID}discharge_update", "data"),
    prevent_initial_call=True,
)
def submit_discharge_status(
    n_clicks: int, discharge: str, node: dict, discharge_update: dict
):
    """Submit discharge status button"""
    disabled = True

    # disable the button on first load of status
    if ctx.triggered_id == f"{BPID}tap_node":
        return discharge_update, disabled, "primary"
    # enable the button if the discharge radio changes
    elif ctx.triggered_id == f"{BPID}discharge_radio":
        return discharge_update, not disabled, "primary"

    # Proceed if the trigger is the button itself
    encounter = node.get("data").get("encounter")

    # post to baserow table
    # msg = f"Discharge status for encounter {encounter} set to {discharge}"
    # print(msg)

    res = _post_discharge_status(encounter, discharge)
    saved_ok = True if res.dict().get("id") else False

    discharge_update = {encounter: discharge}

    if saved_ok:
        return discharge_update, disabled, "success"
    else:
        return discharge_update, not disabled, "warning"
