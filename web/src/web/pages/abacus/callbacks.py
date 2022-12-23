from typing import Any
import math

from dash import Input, Output, callback, dcc, State
from web.hospital import get_building_departments

# callback functions created here will be labelled with BPID for abacus
from web.pages.abacus import BPID
from web.pages.abacus.utils import (
    _get_beds,
    _get_census,
    _make_bed,
    _populate_beds,
    _list_of_unique_rooms,
    _make_room,
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
def get_beds(department: str) -> dict[str, Any]:
    beds = _get_beds(department=department)
    return beds


@callback(
    Output(f"{BPID}census", "data"),
    Input(f"{BPID}dept_dropdown", "value"),
)
def get_census(department: str) -> dict[str, Any]:
    census = _get_census(department=department)
    return census


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


# @callback([
#     Output(f"{BPID}layout_radio", "value"),
#     Output(f"{BPID}building_radio", "value"),
#     Output(f"{BPID}department_dropdown", "value"),
#     ],
#     Input(f"{BPID}button", "n_clicks"),
#     State(f"{BPID}departments", "data"),
# )
# def reset_all(n_clicks, departments):
#     layout = "random"
#     dept = departments["tower"][0]
#     print(dept)
#     return [
#         layout,
#         "tower",
#         dept,
#     ]

# @callback(
#     Output(f"{BPID}dept_title", "children"),
#     Input(f"{BPID}dept_dropdown", "value"),
# )
# def display_dept_title(department: str):
#     return html.H4(department.title())
#
#
# # @callback(
# #     Output("bed_inspector", "children"),
# #     Input(f"{BPID}bed_map", "tapNode"),
# #     prevent_initial_callback=True,
# # )
# # def tap_bed_inspector(data):
# #     if data:
# #         csn = data.get("data").get("census").get("encounter")
# #         return _provide_patient_detail(csn)
# #     else:
# #         return json.dumps({}, indent=4)
# #
# #
# # @callback(
# #     Output("node_inspector", "children"),
# #     Input(f"{BPID}bed_map", "tapNode"),
# #     prevent_initial_callback=True,
# # )
# # def tap_node_inspector(data):
# #     return json.dumps(data, indent=4)
# #
# #


# @callback(
#     Output(f"{BPID}bed_map", "elements"),
#     Input(f"{BPID}patients_in_beds", "data"),
#     State(f"{BPID}layout_radio", "value"),
#     # prevent_initial_call=True,
# )
# def display_ward_map(
#     elements,
#     layout,
# ):

# @callback(
#     Output(f"{BPID}ward_map", "children"),
#     Input(f"{BPID}patients_in_beds", "data"),
#     State(f"{BPID}layout_radio", "value"),
#     prevent_initial_call=True,
# )
# def display_ward_map(
#     elements,
#     layout,
# ):
#     zoom = 1
#     return cyto.Cytoscape(
#         id=f"{BPID}bed_map",
#         # layout={"name": layout, "fit": True, "padding": 80},
#         layout={"name": layout},
#         style={
#             "width"   : "600px",
#             "height"  : "600px",
#             # "width"   : "42vw",
#             # "height"  : "80vh",
#             "position": "relative",
#             # "top"     : "4vh",
#             # "left"    : "4vw",
#         },
#         stylesheet=[
#             {"selector": "node", "style": {"label": "data(label)"}},
#             {
#                 "selector": "[?occupied]",
#                 "style"   : {
#                     "shape"       : "ellipse",
#                     # "background-color": "#ff0000",
#                     # "background-opacity": 1.0,
#                     "border-width": 2,
#                     "border-style": "solid",
#                     "border-color": "red",
#                 },
#             },
#             {
#                 "selector": '[!occupied][level="bed"]',
#                 "style"   : {
#                     "shape"             : "rectangle",
#                     "background-color"  : "grey",
#                     "background-opacity": 0.2,
#                     "border-width"      : 2,
#                     "border-style"      : "solid",
#                     "border-color"      : "black",
#                 },
#             },
#         ],
#         elements=elements,
#         # responsive=True,
#         # autolock=True,
#         # maxZoom=2,
#         # zoom=zoom,
#         # minZoom=0.2,
#     )
