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

from web.pages.abacus import BPID
# Interfaces with out modules
# ---------------------------
from web.pages.abacus.dept import input_active_dept
from web.pages.abacus.map_utils import (_filter_non_beds, _list_of_unique_rooms,
                                        _make_bed, _make_room, _populate_beds,
                                        _update_discharges,
                                        _update_patients_with_sitrep)
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
                zoomingEnabled=True,  # else won't 'fit'
                minZoom=0.5,
            )
        ]
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
def _gen_layout_radio(dept: str, layout: str) -> tuple[str, list[dict]]:
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

    return layouts.get(layout, {})


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
        elements = [e for e in elements if
                    e.get("data", {}).get("level") != "room"]
        for e in elements:
            e["data"]["id"] = e["data"]["id"] + tag_string
    else:
        tag_string = ""

    if tap_node:
        selected_id = tap_node.get("data", {}).get("id") + tag_string
        for ele in elements:
            ele["selected"] = (
                True if ele.get("data", {}).get("id") == selected_id else False
            )

    return elements


@callback(
    Output(f"{BPID}elements", "data"),
    input_census_data,
    input_beds_data,
    input_sitrep_data,
    Input(f"{BPID}discharge_statuses", "data"),
)
def make_cytoscape_elements(
    census: list[dict],
    beds: list[dict],
    sitrep: list[dict],
    discharges: list[dict],
) -> list[dict]:
    room_list = [_make_room(r) for r in _list_of_unique_rooms(beds)]

    bed_list = [_make_bed(i) for i in _filter_non_beds(beds)]
    bed_list.sort(key=lambda bed: bed.get("data", {}).get("bed_index"))
    bed_list = _populate_beds(bed_list, census)
    bed_list = _update_discharges(bed_list, discharges)

    # if sitlist exists
    if sitrep and sum([len(i) for i in sitrep]):
        bed_list = _update_patients_with_sitrep(bed_list, sitrep)

    elements = bed_list + room_list

    for ele in elements:
        # ele["selected"] = False
        if ele.get("data", {}).get("level") == "room":
            ele["selectable"] = False

    return elements


@callback(
    Output(f"{BPID}tap_node", "data"),
    Input(f"{BPID}bed_map", "tapNode"),
    input_active_dept,
    prevent_initial_call=True,
)
def _store_tap_node(node: dict, _: str) -> dict | None:
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
def _store_selected_nodes(nodes: list[dict], _: str) -> list[dict] | None:
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
        return node.get("data", {}).get("encounter", None)  # noqa
    else:
        return None
