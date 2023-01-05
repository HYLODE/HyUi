"""
Module to draw the cytoscape map based on the department
Exposes
- radio_cyto_layout : dbc.RadioItems to select cytoscape layout
- store_elements
- map_cyto_beds
- input_map_tapnode: data from clicking on a node of the map
- store_encounter
"""
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import math
from dash import Input, Output, State, callback, ctx, dcc, html
from datetime import datetime

from web.pages.abacus import BPID

# Interfaces with out modules
# ---------------------------
from web.pages.abacus.dept import input_active_dept
from web.pages.abacus.stores import (
    input_beds_data,
    input_census_data,
    input_sitrep_data,
)

# NOTE: the following fails b/c circular so must fall back on string identifer
# from web.pages.abacus.discharges import input_discharges
from . import WARDS_WITH_MAPS

_cyto_stylesheet = [
    {
        # labels for nodes
        "selector": "node",
        "style": {"label": "data(label)"},
    },
    {
        # label rooms
        "selector": '[level="room"]',
        "style": {
            "border-width": 1,
            "border-style": "solid",
            "border-color": "black",
            "background-opacity": 0.2,
            "background-color": "FFD6D5",
        },
    },
    {
        # label occupied
        "selector": "[?occupied]",
        "style": {
            "shape": "ellipse",
            "border-width": 2,
            "border-style": "solid",
            "background-opacity": 1.0,
            "background-color": "mapData(wim, 0, 5, #FFD441, #FF2841)",
            "border-color": "#416CFF",
        },
    },
    {
        # label unoccupied beds (not rooms)
        "selector": '[!occupied][level="bed"]',
        "style": {
            "shape": "rectangle",
            "background-color": "grey",
            "background-opacity": 0.2,
            "border-width": 2,
            "border-style": "solid",
            "border-color": "black",
        },
    },
    {
        # label discharges
        "selector": '[?discharge][level="bed"]',
        "style": {
            "border-width": 6,
            "border-style": "solid",
            "border-color": "#00A642",
        },
    },
    {
        # label closed beds
        "selector": "[?closed]",
        "style": {
            "shape": "polygon",
            # box with a slash
            "shape-polygon-points": "-1 1 1 1 1 -1 -1 -1 -1 1 0.9 -0.9",
        },
    },
    {
        # label occupied
        "selector": ":selected:",
        "style": {
            "shape": "star",
            "border-width": 3,
        },
    },
]

store_elements = dcc.Store(id=f"{BPID}elements")

store_encounter = dcc.Store(id=f"{BPID}encounter")
input_encounter = Input(f"{BPID}encounter", "data")

store_tapnode = dcc.Store(id=f"{BPID}tap_node")
input_tapnode = Input(f"{BPID}tap_node", "data")
state_tapnode = State(f"{BPID}tap_node", "data")

store_selected_nodes = dcc.Store(id=f"{BPID}selected_nodes")
input_selected_nodes = Input(f"{BPID}selected_nodes", "data")
state_selected_nodes = State(f"{BPID}selected_nodes", "data")

radio_cyto_layout = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}layout_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group p-1",
                    inline=True,
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

map_cyto_beds = dbc.Card(
    dbc.CardBody(
        [
            cyto.Cytoscape(
                id=f"{BPID}bed_map",
                style={
                    "width": "42vw",
                    "height": "70vh",
                    "position": "relative",
                    "top": "1vh",
                    "left": "1vw",
                },
                stylesheet=_cyto_stylesheet,
                responsive=True,
                maxZoom=1.0,
                minZoom=0.2,
            )
        ]
    )
)


def _as_int(s: int | float | None) -> int | None:
    if s is None:
        return None
    else:
        return int(float(s))


def _populate_beds(bl: list[dict], cl: list[dict]) -> list[dict]:
    """
    Place patients in beds

    Args:
        bl: bed_list
        cl: census_list

    Returns:
        a list of dictionaries to populate elements for Cytoscape
    """
    # convert to dictionary of dictionaries to search / merge
    cd = {i["location_string"]: i for i in cl}
    for bed in bl:
        location_string = bed.get("data").get("id")  # type: ignore
        census = cd.get(location_string, {})  # type: ignore
        bed["data"]["census"] = census
        bed["data"]["encounter"] = _as_int(census.get("encounter", None))
        bed["data"]["occupied"] = True if census.get("occupied", None) else False
    return bl


def _update_patients_with_sitrep(bl: list[dict], sl: list[dict]) -> list[dict]:
    """
    Merge sitlist details on to patient list using encounter key
    Args:
        bl: beds with patients
        sl: sitlist

    Returns:
        updated bed_list holding sitlist data

    """

    # convert to dictionary for searching simply
    sd = {int(i["csn"]): i for i in sl if i["csn"]}
    for bed in bl:
        csn = bed.get("data").get("encounter")
        sitrep = sd.get(csn, {})
        bed["data"]["sitlist"] = sitrep
        bed["data"]["wim"] = sitrep.get("wim_1")
    return bl


def _update_discharges(bl: list[dict], discharges: list[dict]) -> list[dict]:
    # convert to dictionary of dictionaries to search / merge
    dd = {i["csn"]: i for i in discharges}
    for bed in bl:
        csn = bed.get("data").get("encounter")
        # if there's a patient in the bed
        if not csn:
            continue
        # pm = planned_move
        pm_type = bed["data"]["census"].get("pm_type")
        pm_modified = bed["data"]["census"].get("pm_datetime")
        bed["data"]["discharge"] = True if pm_type == "OUTBOUND" else False

        # if there's better info on discharge status
        dc_status = dd.get(csn, {})
        bed["data"]["dc_status"] = dc_status
        if not len(dc_status):
            continue
        dc_modified = dc_status.get("modified_at")
        if not pm_modified:
            bed["data"]["discharge"] = (
                True if dc_status.get("status") == "ready" else False
            )
        else:
            dc_modified = datetime.fromisoformat(dc_modified)
            pm_modified = datetime.fromisoformat(pm_modified)
            if dc_modified > pm_modified:
                bed["data"]["discharge"] = (
                    True if dc_status.get("status") == "ready" else False
                )

    return bl


def _list_of_unique_rooms(beds: list) -> list:
    rooms = [_split_loc_str(bed["location_string"], "room") for bed in beds]
    rooms = list(set(rooms))
    return rooms


def _split_loc_str(s: str, part: str) -> str:
    dept, room, bed = s.split("^")
    if part == "dept":
        return dept
    elif part == "room":
        return room
    elif part == "bed":
        return bed
    else:
        raise ValueError(f"{part} not one of dept/room/bed")


def _make_bed(
    bed: dict, scale: int = 9, offset: tuple[int, int] = (-100, -100)
) -> dict:
    position = {}
    if bed.get("xpos") and bed.get("ypos"):
        position.update(x=bed.get("xpos") * scale + offset[0]),  # type: ignore
        position.update(y=bed.get("ypos") * scale + offset[0]),  # type: ignore

    hl7_bed = _split_loc_str(bed["location_string"], "bed")
    room = _split_loc_str(bed["location_string"], "room")

    try:
        pretty_bed = hl7_bed.split("-")[1]
        try:
            bed_index = int(pretty_bed)
        except ValueError:
            bed_index = 0
    except IndexError:
        pretty_bed = hl7_bed
        bed_index = 0

    data = dict(
        id=bed["location_string"],
        bed_index=bed_index,  # noqa
        label=pretty_bed,
        parent=room,
        level="bed",
        closed=bed.get("closed", False),
        covid=bed.get("covid", False),
    )

    return dict(data=data, position=position)


def _make_room(room: str) -> dict:
    sideroom = False
    try:
        pretty_room = room.split(" ")[1]
        room_type = pretty_room[:2]
        room_number = pretty_room[2:]
        if room_type == "BY":
            label = "Bay "
        elif room_type == "SR":
            label = "Room "
            sideroom = True
        else:
            label = ""
        # noinspection PyAugmentAssignment
        label = label + room_number
    except IndexError:
        label = room

    return dict(
        data=dict(
            id=room,
            label=label,
            sideroom=sideroom,
            level="room",
        )
    )


@callback(
    (
        Output(f"{BPID}layout_radio", "value"),
        Output(f"{BPID}layout_radio", "options"),
    ),
    input_active_dept,
    Input(f"{BPID}layout_radio", "value"),
    prevent_initial_call=True,
)
def _gen_layout_radio(dept: str, layout: int) -> tuple[str, list]:
    """
    Defaults to  Map option if possible and appends to list of radio buttons
    """
    options = [
        {"label": "Circle", "value": "circle"},
        {"label": "Grid", "value": "grid"},
    ]

    if dept in WARDS_WITH_MAPS:
        options.append({"label": "Map", "value": "preset"})

    if ctx.triggered_id == f"{BPID}active_dept":
        layout = "preset" if dept in WARDS_WITH_MAPS else "circle"

    return layout, options


@callback(
    Output(f"{BPID}bed_map", "layout"),
    Input(f"{BPID}layout_radio", "value"),
)
def _update_layout(layout: str) -> dict:
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
    State(f"{BPID}tap_node", "data"),
    prevent_initial_call=True,
)
def _update_elements_for_layout(
    layout: str,
    elements: list[dict],
    tap_node: dict,
) -> list[dict]:
    """
    Updating the element ID to force a diff
    ---------------------------------------
    Detailed notes in comment below but in brief this forces the 'id' of the
    element to be different for all 'non'-preset layouts; so when preset is
    called cytoscape sees this as a new set of elements and redraws from
    scratch
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
        tag_string = "_"
        elements = [e for e in elements if e.get("data").get("level") != "room"]
        for e in elements:
            e["data"]["id"] = e["data"]["id"] + tag_string
    else:
        tag_string = ""

    if tap_node:
        selected_id = tap_node.get("data").get("id") + tag_string
        for ele in elements:
            ele["selected"] = (
                True if ele.get("data").get("id") == selected_id else False
            )

    return elements


@callback(
    Output(f"{BPID}elements", "data"),
    input_census_data,
    input_beds_data,
    input_sitrep_data,
    Input(f"{BPID}discharge_statuses", "data"),
)
def make_cytoscape_elements(census, beds, sitrep, discharges):
    room_list = [_make_room(r) for r in _list_of_unique_rooms(beds)]

    bed_list = [_make_bed(i) for i in beds]
    bed_list.sort(key=lambda bed: bed.get("data").get("bed_index"))
    bed_list = _populate_beds(bed_list, census)
    bed_list = _update_discharges(bed_list, discharges)

    # if sitlist exists
    if sitrep and sum([len(i) for i in sitrep]):
        bed_list = _update_patients_with_sitrep(bed_list, sitrep)

    elements = bed_list + room_list

    for ele in elements:
        # ele["selected"] = False
        if ele.get("data").get("level") == "room":
            ele["selectable"] = False

    return elements


@callback(
    Output(f"{BPID}tap_node", "data"),
    Input(f"{BPID}bed_map", "tapNode"),
    input_active_dept,
    prevent_initial_call=True,
)
def _store_node(node: dict, _: str) -> dict | None:
    if ctx.triggered_id == f"{BPID}bed_map":
        return node
    else:
        return None


@callback(
    Output(f"{BPID}selected_nodes", "data"),
    Input(f"{BPID}bed_map", "selectedNodeData"),
    input_active_dept,
    prevent_initial_call=True,
)
def _store_node(nodes: list[dict], _: str) -> list[dict] | None:
    "Use this to define how many nodes are selected"
    # if nodes:
    #     print(len(nodes))
    if ctx.triggered_id == f"{BPID}bed_map":
        return nodes
    else:
        return None


@callback(
    Output(f"{BPID}encounter", "data"),
    Input(f"{BPID}bed_map", "tapNode"),
    input_active_dept,
    prevent_initial_call=True,
)
def _store_encounter(node: dict, _: str) -> str | None:
    if ctx.triggered_id == f"{BPID}bed_map":
        return node.get("data").get("encounter", None)
    else:
        return None
