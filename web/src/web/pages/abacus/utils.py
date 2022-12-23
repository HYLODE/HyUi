"""
assorted functions for preparing and running the sitrep data
"""
import json
import requests
import warnings
from requests.exceptions import ConnectionError

from models.beds import Bed
from models.census import CensusRow
from models.sitrep import SitrepRow
from web.config import get_settings
from web.pages.abacus import DEPARTMENT_WARD_MAPPINGS


def _as_int(s: int | float | None) -> int | None:
    if s is None:
        return None
    else:
        return int(float(s))


def _get_beds(department: str) -> list[dict]:
    """
    get bed data from baserow store
    :param department:
    :return: list of beds
    """
    response = requests.get(
        f"{get_settings().api_url}/beds/", params={"department": department}
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


def _get_census(department: str) -> list[dict]:
    """
    get census data for the selected department
    :param department: department in long form (e.g. UCH T03 INTENSIVE CARE)
    :return: list of CensusRow models
    """
    # note that the census API expects a list of departments but you only
    # want one
    departments = [department]
    response = requests.get(
        f"{get_settings().api_url}/census/", params={"departments": departments}
    )
    return [CensusRow.parse_obj(row).dict() for row in response.json()]


def _get_sitrep_status(department: str) -> object:
    """
    get organ support data from old sitrep interface
    :param department:
    :return: original covid sitrep organ support
    """
    # FIXME 2022-12-20 hack to keep this working whilst waiting on
    COVID_SITREP = True
    warnings.warn("Working from old hycastle sitrep", category=DeprecationWarning)

    def _which_sitrep(dept, covid_sitrep: bool = COVID_SITREP):
        if covid_sitrep:
            url = f"http://uclvlddpragae07:5006/live/icu/{dept}/ui"
        else:
            url = f"{get_settings().api_url}/sitrep/live/{dept}/ui"
        return url

    try:
        department = DEPARTMENT_WARD_MAPPINGS[department]
        sitrep_api = _which_sitrep(department)
        response = requests.get(sitrep_api).json().get("data")
    except ConnectionError:
        try:
            department = DEPARTMENT_WARD_MAPPINGS[department]
        except KeyError:
            if department not in DEPARTMENT_WARD_MAPPINGS.values():
                raise KeyError(f"{department} not recognised as valid department")
        sitrep_api = _which_sitrep(department)
        response = requests.get(sitrep_api).json()
    return [SitrepRow.parse_obj(row).dict() for row in response]


def _populate_beds(bed_list: list[dict], census_list: list[dict]) -> list[dict]:
    """
    place patients in beds
    :param bed_list: derived from baserow structure
    :param census_list:
    :return: a list of dictionaries to populate elements for Cytoscape
    """
    # copy the lists first since they are mutable
    bl = bed_list.copy()
    cl = census_list.copy()

    # convert to dictionary of dictionaries to search / merge
    cd = {i["location_string"]: i for i in cl}
    for bed in bl:
        location_string = bed.get("data").get("id")  # type: ignore
        census = cd.get(location_string, {})  # type: ignore
        bed["data"]["census"] = census
        bed["data"]["occupied"] = True if census.get("occupied", None) else False
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


def _make_bed(bed: dict, preset: bool = True, scale: int = 9) -> dict:
    hl7_bed = _split_loc_str(bed["location_string"], "bed")
    try:
        pretty_bed = hl7_bed.split("-")[1]
        try:
            bed_index = int(pretty_bed)
        except ValueError:
            bed_index = 0
    except IndexError:
        pretty_bed = hl7_bed
    room = _split_loc_str(bed["location_string"], "room")
    data = dict(
        id=bed["location_string"],
        bed_index=bed_index,  # noqa
        label=pretty_bed,
        parent=room,
        level="bed",
        closed=bed.get("closed", False),
        covid=bed.get("covid", False),
    )
    if preset:
        if bed.get("xpos") and bed.get("ypos"):
            position = dict(
                x=bed.get("xpos") * scale,  # type: ignore
                y=bed.get("ypos") * scale,  # type: ignore
            )
        else:
            position = dict(
                x=100,
                y=100,
            )
        return dict(data=data, position=position)
    else:
        return dict(data=data)


def _make_room(room: str, preset=True) -> dict:
    sideroom = False
    label = ""
    visible = False

    if preset:
        visible = True
        try:
            pretty_room = room.split(" ")[1]
            room_type = pretty_room[:2]
            room_number = pretty_room[2:]
            if room_type == "BY":
                label = "Bay "
                sideroom = True
            elif room_type == "SR":
                label = "Room "
            else:
                label = ""
            # noinspection PyAugmentAssignment
            label = label + room_number
        except IndexError:
            label = room

    return dict(
        data=dict(
            id=room, label=label, sideroom=sideroom, level="room", visible=visible
        )
    )


def _present_patient(census: dict) -> str:
    """
    Prettify node data
    """

    try:
        date_of_birth = (census.get("date_of_birth").strftime("%d %b %Y"),)
    except AttributeError:
        date_of_birth = "Unknown"
        # object has no attribute 'get': instantiates as object but convert
        # to dict
    return json.dumps(
        dict(
            csn=census.get("encounter"),
            # n_inotropes_1_4h=organ_support.get("n_inotropes_1_4h", ""),
            # had_rrt_1_4h=organ_support.get("had_rrt_1_4h", ""),
            # vent_type_1_4h=organ_support.get("vent_type_1_4h", ""),
            mrn=census.get("mrn"),
            date_of_birth=date_of_birth,
            encounter=census.get("encounter"),
            lastname=census.get("lastname"),
            firstname=census.get("firstname"),
            sex=census.get("sex"),
        ),
        indent=4,
    )
