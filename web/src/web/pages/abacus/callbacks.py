import json
import math
import pytz
import warnings
from dash import Input, Output, State, callback, ctx
from datetime import datetime

from models.beds import DischargeStatus
from web.hospital import get_building_departments

# callback functions created here will be labelled with BPID for abacus
from web.pages.abacus import BPID
from web.pages.abacus.utils import (
    _display_patient,
    _get_beds,
    _get_census,
    _get_discharge_updates,
    _get_perrt_long,
    _get_sitrep_status,
    _list_of_unique_rooms,
    _make_bed,
    _make_room,
    _most_recent_row_only,
    _populate_beds,
    _post_discharge_status,
    _update_discharges,
    _update_patients_with_sitrep,
)
from . import SITREP_DEPT2WARD_MAPPING, WARDS_WITH_MAPS


@callback(
    Output(f"{BPID}departments", "data"),
    Input(f"{BPID}page_interval", "n_intervals"),
    background=True,
)
def store_all_departments(_: int):
    """
    Store a list of departments for the building
    Triggers the update of most of the elements on the page
    """
    building_departments = get_building_departments()
    return [bd.dict() for bd in building_departments]


@callback(
    (
        Output(f"{BPID}dept_dropdown", "options"),
        Output(f"{BPID}dept_dropdown", "value"),
    ),
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
    options = [{"label": v, "value": v} for v in dropdown]

    return options, dropdown[0]


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
    (
        Output(f"{BPID}layout_radio", "value"),
        Output(f"{BPID}layout_radio", "options"),
    ),
    Input(f"{BPID}dept_dropdown", "value"),
    Input(f"{BPID}layout_radio", "value"),
    prevent_initial_call=True,
)
def set_layout_radio(dept: str, layout: int) -> tuple[str, list]:
    """
    Defaults to  Map option if possible and appends to list of radio buttons
    """
    options = [
        {"label": "Circle", "value": "circle"},
        {"label": "Grid", "value": "grid"},
    ]

    if dept in WARDS_WITH_MAPS:
        options.append({"label": "Map", "value": "preset"})

    if ctx.triggered_id == f"{BPID}dept_dropdown":
        layout = "preset" if dept in WARDS_WITH_MAPS else "circle"

    return layout, options


@callback(
    Output(f"{BPID}bed_map", "layout"),
    Input(f"{BPID}layout_radio", "value"),
)
def update_layout(layout: str) -> dict:
    """
    Set cytoscape layout parameters
    """

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
        "grid": {
            "name": "grid",
            "animate": True,
            "fit": True,
            "padding": 10,
            "cols": 5,
        },
    }

    return layouts.get(layout)


@callback(
    Output(f"{BPID}bed_map", "elements"),
    Input(f"{BPID}layout_radio", "value"),
    Input(f"{BPID}elements", "data"),
    prevent_initial_call=True,
)
def update_elements_for_layout(
    layout: str,
    elements: list[dict],
) -> list[dict]:
    """
    Updating the element ID to force a diff
    ---------------------------------------
    Detailed notes in comment below but in brief this forces the 'id' of the
    element to be different for all 'non'-preset layouts; so when preset is
    called cytoscape sees this as a new set of elements and redraws from scratch
    """
    # Switching _back_ to a preset layout has no effect as per
    # https://github.com/plotly/react-cytoscapejs/issues/3#issuecomment
    # -430070424
    # b/c preset is a 'null-op' so only runs the first time
    # see also
    # https://github.com/plotly/react-cytoscapejs/issues/7
    # https://github.com/plotly/dash-cytoscape/issues/33
    # Fixes attempted
    # - reload the whole page when preset layout selected
    # - capture the renderedPosition of each element and use this
    # - rebuild layout with some 'change' to force a diff

    if layout != "preset":
        elements = [e for e in elements if e.get("data").get("level") != "room"]
        for e in elements:
            e["data"]["id"] = e["data"]["id"] + "_"

    return elements


@callback(
    Output(f"{BPID}elements", "data"),
    Input(f"{BPID}census", "data"),
    Input(f"{BPID}beds", "data"),
    Input(f"{BPID}sitrep", "data"),
    Input(f"{BPID}discharge_statuses", "data"),
)
def make_cytoscape_elements(census, beds, sitrep, discharges):
    room_list = [_make_room(r) for r in _list_of_unique_rooms(beds)]

    bed_list = [_make_bed(i) for i in beds]
    bed_list.sort(key=lambda bed: bed.get("data").get("bed_index"))
    bed_list = _populate_beds(bed_list, census)
    bed_list = _update_discharges(bed_list, discharges)

    # if sitrep exists
    if sitrep and sum([len(i) for i in sitrep]):
        bed_list = _update_patients_with_sitrep(bed_list, sitrep)

    elements = bed_list + room_list

    # Update elements so that none selected on first instantiation I think this
    # works b/c elements is a mutable list so we are actually modifying its
    # contents
    for ele in elements:
        ele["selected"] = False
        if ele.get("data").get("level") == "room":
            ele["selectable"] = False

    return elements


@callback(
    Output(f"{BPID}discharge_statuses", "data"),
    Input(f"{BPID}page_interval", "n_intervals"),
    Input(f"{BPID}discharge_submit_button", "n_clicks"),
    State(f"{BPID}discharge_statuses", "data"),
    State(f"{BPID}discharge_radio", "value"),
    State(f"{BPID}tap_node", "data"),
    background=True,
)
def store_discharge_statuses(
    n_intervals: int,
    n_clicks: int,
    dc_statuses: list[dict],
    dc_radio: str,
    node: dict,
) -> list[dict]:
    if ctx.triggered_id == f"{BPID}discharge_submit_button":
        all_updates = dc_statuses
        all_updates.append(
            dict(
                csn=node.get("data").get("encounter"),
                status=dc_radio,
                modified_at=datetime.now(tz=pytz.UTC).isoformat(),
            )
        )
    else:
        all_updates = _get_discharge_updates()
    return _most_recent_row_only(
        all_updates,
        groupby_col="csn",
        timestamp_col="modified_at",
        data_model=DischargeStatus,  # noqa
    )


@callback(
    Output(f"{BPID}discharge_radio", "value"),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_call=True,
)
def set_discharge_radio(node: dict):
    """sets discharge status"""
    status = None
    if any(node) and node.get("data").get("dc_status"):
        status = node.get("data").get("dc_status").get("status")
        status = status if status else "no"
    return status


@callback(
    (
        Output(f"{BPID}discharge_submit_button", "disabled"),
        Output(f"{BPID}discharge_submit_button", "color"),
    ),
    Input(f"{BPID}discharge_submit_button", "n_clicks"),
    Input(f"{BPID}discharge_radio", "value"),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_call=True,
)
def submit_discharge_status(
    n_clicks: int,
    radio_status: str,
    node: dict,
) -> tuple[bool, str]:
    """
    Submit discharge status button
    Function has two roles
    1. submit using requests.post
    2. manage the colour and enable/disable status of the submit button
    """
    if any(node):
        node_status = node.get("data", {}).get("dc_status", {}).get("status", None)
    else:
        node_status = None
    btn_disabled = True if radio_status == node_status else False
    btn_color = "primary"

    if ctx.triggered_id == f"{BPID}discharge_submit_button":
        encounter = node.get("data").get("encounter")
        res = _post_discharge_status(encounter, radio_status)
        saved_ok = True if res.dict().get("id") else False
        if saved_ok:
            btn_disabled = True
            btn_color = "success"
        else:
            # TODO: display some sort of alert as flash message
            btn_disabled = True
            btn_color = "warning"

    return btn_disabled, btn_color


@callback(
    (
        Output(f"{BPID}bed_inspector_header", "children"),
        Output(f"{BPID}bed_inspector_body", "children"),
    ),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_callback=True,
)
def tap_bed_inspector(element: dict):
    if element and any(element):
        data = element.get("data")
        return _display_patient(data)
    else:
        return "", ""


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
    Output(f"{BPID}node_debug", "children"),
    Input(f"{BPID}tap_node", "data"),
    prevent_initial_callback=True,
)
def tap_debug_inspector(data: dict):
    return json.dumps(data, indent=4)


@callback(
    (
        Output(f"{BPID}pts_now_slider", "value"),
        Output(f"{BPID}pts_now_slider", "max"),
    ),
    Input(f"{BPID}elements", "data"),
    prevent_initial_callback=True,
)
def show_patients_now(elements: dict):
    n = sum([True for e in elements if e.get("data").get("occupied")])
    return n, 35


@callback(
    (
        Output(f"{BPID}pts_next_slider", "min"),
        Output(f"{BPID}pts_next_slider", "value"),
        Output(f"{BPID}pts_next_slider", "max"),
    ),
    Input(f"{BPID}pts_now_slider", "value"),
    Input(f"{BPID}dcs_confirmed", "value"),
    Input(f"{BPID}adm_confirmed", "value"),
    Input(f"{BPID}adm_expected", "value"),
    prevent_initial_callback=True,
)
def show_patients_next(now: int, dcs: int, adm_con: int, adm_exp: int):
    """
    Values to ba passed to the RangeSlider component
    Args:
        now:
        dcs:
        adm_con:
        adm_exp:

    Returns:

    """
    next = now - dcs + adm_con + adm_exp
    next_upper = next + 1
    next_lower = next - 1

    slider_min = next - 5
    slider_max = next + 5

    return 0, [next_lower, next_upper], 35


@callback(
    (
        Output(f"{BPID}dcs_ready", "value"),
        Output(f"{BPID}dcs_ready", "max"),
        Output(f"{BPID}dcs_confirmed", "max"),
    ),
    Input(f"{BPID}elements", "data"),
    prevent_initial_callback=True,
)
def show_dcs_ready(elements: dict):
    n = sum([True for e in elements if e.get("data").get("discharge")])
    n_max = 5 * ((n // 5) + 1)  # multiple of 5 above n
    return n, n_max, n_max


@callback(
    Output(f"{BPID}dcs_confirmed", "value"),
    Input(f"{BPID}dcs_ready", "value"),
    State(f"{BPID}dcs_confirmed", "value"),
    prevent_initial_callback=True,
)
def show_dcs_confirmed(ready: int, confirmed: int):
    """
    Placeholder callback that should query the number of confirmed discharges
    """
    if confirmed is not None:
        return confirmed
    else:
        return 0


@callback(
    Output(f"{BPID}ward_status", "className"),
    Input(f"{BPID}pts_next_slider", "value"),
    Input(f"{BPID}pts_now_slider", "value"),
    State(f"{BPID}ward_status", "className"),
    prevent_initial_callback=True,
)
def show_highlight_occupancy(pts_next: list[int], pts_now: int, info_class: str):
    """ """
    next_lower, next_upper = pts_next
    if next_upper > pts_now:
        color = "danger"
    elif next_upper < pts_now:
        color = "success"
    else:
        color = "info"

    _default = "border rounded border-2 p-2"
    return "border-" + color + " " + _default
