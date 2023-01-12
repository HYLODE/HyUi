import json
import math
import pandas as pd
import requests
from dash import Input, Output, callback

from models.census import CensusRow
from web.config import get_settings
from web.pages.home import ids
from web.stores import ids as store_ids


@callback(
    Output(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.DEPT_STORE, "data"),
)
def _store_depts(campus: str, depts: list[dict]) -> list[dict]:
    """Need a list of departments for this building"""
    return [dept for dept in depts if dept.get("location_name") == campus]


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.DEPT_STORE, "data"),
    Input(store_ids.BEDS_STORE, "data"),
)
def _store_beds(campus: str, depts: list[dict], beds: list[dict]) -> list[dict]:
    """
    Return a list of beds for that campus
    - merge in departments to drop closed departments
    - generate the floor_index from the bed_number to permit appropriate sorting
    """

    dfbeds = pd.DataFrame.from_records(beds)
    dfdepts = pd.DataFrame.from_records(depts)
    dfdepts = dfdepts[["department", "floor_order"]]

    # inner join to drop closed_perm_01
    beds = dfbeds.merge(dfdepts, on="department", how="inner")
    # drop beds other than those for this campus
    mask = beds["location_name"] == campus
    beds = beds[mask]

    beds = beds[beds["bed_number"] != -1]
    beds = beds[~beds["closed"]]

    def _gen_floor_indices(df: pd.DataFrame) -> pd.DataFrame:
        # now generate floor_y_index
        df.sort_values(
            ["floor", "floor_order", "department", "bed_number"], inplace=True
        )
        floor_depts = df[["floor", "floor_order", "department"]].drop_duplicates()
        floor_depts.sort_values(["floor", "floor_order"], inplace=True)
        floor_depts["floor_y_index"] = floor_depts.reset_index().index + 1
        df = df.merge(floor_depts, how="left")

        # create a floor x_index by sorting and ranking within floor_y_index
        df.sort_values(["floor_y_index", "bed_number"], inplace=True)
        df["floor_x_index"] = df.groupby("floor_y_index")["bed_number"].rank(
            method="first", na_option="keep"
        )
        df.sort_values(["location_string"], inplace=True)
        return df

    beds = _gen_floor_indices(beds)

    res: list[dict] = beds.to_dict(orient="records")
    return res


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
        # you could use the grid layout with invisible beds to create maps
        "grid": {
            "name": "grid",
            "animate": True,
            "fit": True,
            "padding": 10,
            # "cols": 5,
        },
        # "concentric": {
        #     "name": "concentric",
        #     "animate": True,
        #     "fit": True,
        #     "padding": 10,
        #     "concentric": "function(floor){floor}"
        # },
        # "breadthfirst": {
        #     "name": "breadthfirst",
        #     "animate": True,
        #     "fit": True,
        #     "padding": 10,
        # },
        # "cose": {
        #     "name": "cose",
        #     "animate": True,
        #     "fit": True,
        #     "padding": 10,
        # },
    }
    return layouts.get(val, {})


@callback(
    Output(ids.CYTO_MAP, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    # Todo: remove these room and dept set_stores since now in the baserow defn
    Input(ids.ROOM_SET_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.BEDS_STORE, "data"),
    background=True,
)
def _prepare_cyto_elements(
    census: list[dict],
    rooms: list[str],
    depts: list[dict],
    beds: list[dict],
) -> list[dict]:
    elements = list()

    # create beds
    for bed in beds:
        data = dict(
            id=bed.get("location_string"),
            bed_number=bed.get("bed_number"),
            bed_index=bed.get("bed_index"),
            floor=bed.get("floor"),
            entity="bed",
            parent=bed.get("department"),
            bed=bed,
        )
        position = dict(
            x=bed.get("floor_x_index", -1) * 40,
            # subtract from 20 so the 'top floor' is drawn first (origin is
            # upper, left)
            y=(20 - bed.get("floor_y_index", -1)) * 60,
        )
        elements.append(dict(data=data, position=position))

    for dept in depts:
        data = dict(
            id=dept.get("department"),
            label=dept.get("department"),
            entity="department",
            dept=dept,
        )
        elements.append(dict(data=data))

    # for bed in census:
    #     location_string = bed.get("location_string")
    #     if not location_string:
    #         continue
    #
    #     data = dict(
    #         id=location_string,
    #         occupied=bed.get("occupied", False),
    #         parent="^".join(location_string.split("^")[:2]),
    #         entity="bed",
    #     )
    #
    #     elements.append(dict(data=data))
    #
    # for room in rooms:
    #     dept = room.split("^")[0]
    #     data = dict(
    #         id=room,
    #         parent=dept,
    #         entity="room",
    #     )
    #     elements.append(dict(data=data))
    #

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
