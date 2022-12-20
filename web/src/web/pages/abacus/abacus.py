"""
sub-application for the abacus endpoint
"""

import json
import warnings

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import requests
from requests.exceptions import ConnectionError
from dash import Input, Output, callback, html, register_page

from models.beds import Bed
from models.census import CensusRow
from models.sitrep import SitrepRow
from web.config import get_settings
from web.pages.abacus import DEPARTMENT_WARD_MAPPINGS, styles

register_page(__name__, name="ABACUS")
DEPARTMENT = "UCH T03 INTENSIVE CARE"


def get_sitrep_organ_support(department: str = DEPARTMENT) -> object:
    try:
        # FIXME 2022-12-20 hack to keep this working whilst waiting on
        department = DEPARTMENT_WARD_MAPPINGS[department]
        response = requests.get(f"http://uclvlddpragae07:5006/live/icu/{department}/ui")
        response = response.json().get("data")
        warnings.warn("Working from old hycastle sitrep", category=DeprecationWarning)
    except ConnectionError:
        try:
            department = DEPARTMENT_WARD_MAPPINGS[department]
        except KeyError:
            if department not in DEPARTMENT_WARD_MAPPINGS.values():
                raise KeyError(f"{department} not recognised as valid department")
        response = requests.get(f"{get_settings().api_url}/sitrep/live/{department}/ui")
        response = response.json()
    return [SitrepRow.parse_obj(row).dict() for row in response]


def get_census(department: str = DEPARTMENT) -> object:
    # note that the census API expects a list of departments but you only
    # want one
    departments = [department]
    response = requests.get(
        f"{get_settings().api_url}/census/", params={"departments": departments}
    )
    return [CensusRow.parse_obj(row).dict() for row in response.json()]


def get_beds(department: str = DEPARTMENT):
    response = requests.get(
        f"{get_settings().api_url}/beds/", params={"department": department}
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


def list_of_unique_rooms(beds: list) -> list:
    rooms = [split_loc_str(bed["location_string"], "room") for bed in beds]
    rooms = list(set(rooms))
    return rooms


def split_loc_str(s: str, part: str) -> str:
    dept, room, bed = s.split("^")
    if part == "dept":
        return dept
    elif part == "room":
        return room
    elif part == "bed":
        return bed
    else:
        raise ValueError(f"{part} not one of dept/room/bed")


def make_bed(d: dict):
    bed = split_loc_str(d["location_string"], "bed")
    pretty_bed = bed.split("-")[1]
    room = split_loc_str(d["location_string"], "room")
    return dict(
        data=dict(
            id=d["location_string"],
            label=pretty_bed,
            parent=room,
            level="bed",
        ),
        position=dict(x=d["xpos"] * 10, y=d["ypos"] * 10),
    )


def make_room(room: str) -> dict:
    pretty_room = room.split(" ")[1]
    sideroom = False
    if pretty_room[:2] == "BY":
        label = "Bay " + pretty_room[2:]
    elif pretty_room[:2] == "SR":
        label = "Room"
        sideroom = True
    else:
        label = pretty_room

    return dict(data=dict(id=room, label=label, sideroom=sideroom, level="room"))


def populate_beds(bed_list: list[dict], census: list[dict]) -> list[dict]:
    """
    place patients in beds
    :param bed_list: derived from baserow structure
    :param census:
    :return:
    """
    # convert to dictionary of dictionaries to search / merge
    census = {i["location_string"]: i for i in census}
    for bed in bed_list:
        location_string = bed.get("data").get("id")
        bed["data"]["census"] = census.get(location_string, {})
        if bed.get("data").get("census").get("occupied"):
            bed.get("data")["occupied"] = True
        else:
            bed.get("data")["occupied"] = False
    return bed_list


def _as_int(s: int | float | None) -> int | None:
    if s is None:
        return None
    else:
        return int(float(s))


def provide_patient_detail(csn: int) -> str:
    """
    Provide as much detail on the specific patient as possible
    :return:
    """
    # ensure that csn is an integer before using as key
    if csn is None:
        return json.dumps({})
    csn = _as_int(csn)

    # FIXME: DRY: save these calls as dcc.Store
    census = get_census()
    census = [i for i in census if _as_int(i["encounter"]) == csn]
    if len(census) == 0:
        raise ValueError(f"Episode {csn} not found in census")
    elif len(census) == 1:
        census = census[0]
    else:
        raise ValueError(f"Duplicate episodes for {csn} found in census")

    organ_support = get_sitrep_organ_support()
    organ_support = [i for i in organ_support if _as_int(i["csn"]) == csn]
    if len(organ_support) == 0:
        warnings.warn(f"Episode {csn} not found in organ support")
        organ_support = {}
    elif len(organ_support) == 1:
        organ_support = organ_support[0]
    else:
        raise ValueError(f"Duplicate episodes for {csn} found in sitrep organ support")

    # json dumps to convert to string since you're writing to html.Pre
    # object has no attribute 'get': instantiates as object but convert to dict
    return json.dumps(
        dict(
            csn=csn,
            n_inotropes_1_4h=organ_support.get("n_inotropes_1_4h", ""),
            had_rrt_1_4h=organ_support.get("had_rrt_1_4h", ""),
            vent_type_1_4h=organ_support.get("vent_type_1_4h", ""),
            mrn=census.get("mrn"),
            encounter=census.get("encounter"),
            date_of_birth=census.get("date_of_birth").strftime("%d %b %Y"),
            lastname=census.get("lastname"),
            firstname=census.get("firstname"),
            sex=census.get("sex"),
        ),
        indent=4,
    )


@callback(
    Output("bed_inspector", "children"),
    Input("bed_map", "tapNode"),
    prevent_initial_callback=True,
)
def displayTapNode(data):
    if data:
        csn = data.get("data").get("census").get("encounter")
        return provide_patient_detail(csn)
    else:
        return json.dumps({}, indent=4)


@callback(
    Output("node_inspector", "children"),
    Input("bed_map", "tapNode"),
    prevent_initial_callback=True,
)
def displayTapNode(data):
    return json.dumps(data, indent=4)


beds = get_beds()
room_list = [make_room(r) for r in list_of_unique_rooms(beds)]
bed_list = [make_bed(i) for i in beds]

census = get_census()
bed_list = populate_beds(bed_list, census)

organ_support = get_sitrep_organ_support()
provide_patient_detail(census[1].get("encounter"))

nodes = room_list + bed_list
edges = []

cyto_map = html.Div(
    [
        cyto.Cytoscape(
            id="bed_map",
            layout={"name": "preset"},
            style={
                "width": "42vw",
                "height": "80vh",
                "position": "absolute",
                "top": "4vh",
                "left": "4vw",
            },
            stylesheet=[
                {"selector": "node", "style": {"label": "data(label)"}},
                {
                    "selector": "[?occupied]",
                    "style": {
                        "shape": "circle",
                        # "background-color": "#ff0000",
                        # "background-opacity": 1.0,
                        "border-width": 2,
                        "border-style": "solid",
                        "border-color": "red",
                    },
                },
                {
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
            ],
            elements=nodes + edges,
            responsive=True,
            autolock=True,
            maxZoom=2,
            minZoom=0.5,
        )
    ]
)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [html.H2(DEPARTMENT), cyto_map],
                        md={"size": 6},
                    ),
                    dbc.Col(
                        [
                            html.H2("Bed Inspector"),
                            html.Pre(id="bed_inspector", style=styles["pre"]),
                            html.Pre(id="node_inspector", style=styles["pre"]),
                        ],
                        md={"size": 6},
                    ),
                ]
            )
        ]
    )
