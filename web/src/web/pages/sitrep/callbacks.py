import json
import json
import math
import pandas as pd
import requests
from dash import Input, Output, callback, State

from models.census import CensusRow
from web.config import get_settings
from web.pages.sitrep import CAMPUSES, ids
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
    Output(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
)
def _dept_open_store_names(depts_open: list[dict]) -> list[str]:
    return [i.get("department") for i in depts_open]


@callback(
    Output(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(store_ids.ROOM_STORE, "data"),
    Input(store_ids.BEDS_STORE, "data"),
)
def _store_rooms(depts: list[dict], rooms: list[dict], beds: list[dict]) -> list[dict]:
    """Need a list of rooms for departments in this building"""
    # TODO: drop rooms where all beds are closed
    # TODO: better don't show rooms at the campus layout; the 'selector'
    #  should then respond to the level of your view (i.e. campus at ward
    #  overview, and ward at ward level with a 'back' option)
    dfbeds = pd.DataFrame.from_records(beds)
    dfrooms = pd.DataFrame.from_records(rooms)
    dfdepts = pd.DataFrame.from_records(depts)

    dfdepts = dfdepts[["department", "closed_perm_01"]]
    dfrooms = dfrooms.merge(dfdepts, on="department")

    room_closed_status = dfbeds.groupby("hl7_room")["closed"].all()
    room_closed_status = pd.DataFrame(room_closed_status).reset_index()
    dfrooms = dfrooms.merge(room_closed_status, on="hl7_room")

    return dfrooms.to_dict(orient="records")


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.DEPT_STORE, "data"),
    Input(store_ids.ROOM_STORE, "data"),
    Input(store_ids.BEDS_STORE, "data"),
)
def _store_beds(
    campus: str,
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
) -> list[dict]:
    """
    Return a list of beds for that campus
    - merge in departments to drop closed departments
    - generate the floor_index from the bed_number to permit appropriate sorting
    """

    dfdepts = pd.DataFrame.from_records(depts)
    dfdepts = dfdepts[["department", "floor_order"]]
    dfrooms = pd.DataFrame.from_records(rooms)
    dfrooms = dfrooms[["hl7_room", "is_sideroom"]]

    bedsdf = pd.DataFrame.from_records(beds)
    # inner join to drop rooms without beds
    bedsdf = bedsdf.merge(dfrooms, on="hl7_room", how="inner")
    # inner join to drop closed_perm_01
    bedsdf = bedsdf.merge(dfdepts, on="department", how="inner")

    # drop beds other than those for this campus
    mask = bedsdf["location_name"] == campus
    bedsdf = bedsdf[mask]

    bedsdf = bedsdf[bedsdf["bed_number"] != -1]
    bedsdf = bedsdf[~bedsdf["closed"]]

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

    bedsdf = _gen_floor_indices(bedsdf)

    res: list[dict] = bedsdf.to_dict(orient="records")
    return res


@callback(
    Output(ids.CENSUS_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    # background=True,
)
def _store_census(
    campus: str,
    depts_open_names: list[str],
) -> list[dict]:
    """
    Store CensusRow as list of dictionaries after filtering out closed
    departments for that building
    Args:
        campus: one of UCH/WMS/GWB/NHNN
        depts_open_names: list of departments that are open

    Returns:
        Filtered list of CensusRow dictionaries

    """
    campus_short_name = [i.get("label") for i in CAMPUSES if i.get("value") == campus][
        0
    ]

    response = requests.get(
        f"{get_settings().api_url}/census/campus/",
        params={"campuses": campus_short_name},
    )

    res = [CensusRow.parse_obj(row).dict() for row in response.json()]
    res = [row for row in res if row.get("department") in depts_open_names]
    return res


@callback(
    Output(ids.CYTO_WARD_CYTO, "layout"),
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
        # you could use the grid layout with invisible beds to create maps
        "grid": {
            "name": "grid",
            "animate": True,
            "fit": True,
            "padding": 10,
            # "cols": 5,
        },
    }
    layout = layouts.get(val, {})
    return layout


@callback(
    [
        Output(ids.DEPT_SELECTOR, "data"),
        Output(ids.DEPT_SELECTOR, "value"),
    ],
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
)
def _dept_control(depts: list[str], campus: str) -> (list[str], str):
    default = [i.get("default_dept") for i in CAMPUSES if i.get("value") == campus][0]
    return depts, default


def _make_elements(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    selected_dept: str,
    selected_tab: str,
) -> list[dict]:
    # Start with an empty list of elements to populate
    elements = list()
    y_index_max = max([bed.get("floor_y_index", -1) for bed in beds])

    census_d = {i.get("location_string"): i for i in census}

    # show either rooms or department as parent but not both
    if selected_tab == "campus":
        show_rooms = False
    elif selected_tab == "ward":
        show_rooms = True
    else:
        raise NotImplementedError

    show_depts = not show_rooms
    bed_parent = "hl7_room" if show_rooms else "department"

    # create beds
    for bed in beds:
        department = bed.get("department")
        if selected_tab != "campus" and department != selected_dept:
            continue
        location_string = bed.get("location_string")
        data = dict(
            id=location_string,
            bed_number=bed.get("bed_number"),
            bed_index=bed.get("bed_index"),
            department=department,
            floor=bed.get("floor"),
            entity="bed",
            parent=bed.get(bed_parent),
            bed=bed,
            census=census_d.get(location_string, {}),
            closed=bed.get("closed"),
            occupied=census_d.get(location_string, {}).get("occupied", "False"),
        )
        position = dict(
            x=bed.get("floor_x_index", -1) * 40,
            # subtract from 20 so the 'top floor' is drawn first (origin is
            # upper, left)
            y=(y_index_max - bed.get("floor_y_index", -1)) * 60,
        )
        elements.append(
            dict(
                data=data,
                position=position,
                grabbable=True,
                selectable=True,
                locked=False,
            )
        )

    if show_rooms:
        for room in rooms:
            department = room.get("department")
            hl7_room = room.get("hl7_room")
            if department != selected_dept or room.get("closed"):
                continue
            data = dict(
                id=hl7_room,
                label=room.get("room"),
                entity="room",
                room=room,
                parent=department,
            )
            elements.append(
                dict(
                    data=data,
                    grabbable=True,
                    selectable=False,
                    locked=False,
                )
            )

    if show_depts:
        for dept in depts:
            dept_name = dept.get("department")
            selected = True if dept_name == selected_dept else False
            data = dict(
                id=dept_name,
                label=dept_name,
                entity="department",
                dept=dept,
                parent=dept.get("location_name"),
            )
            elements.append(
                dict(
                    data=data,
                    grabbable=True,
                    selectable=True,
                    locked=False,
                    selected=selected,
                )
            )
    return elements


@callback(
    Output(ids.CYTO_CAMPUS_CYTO, "elements"),
    State(ids.CENSUS_STORE, "data"),
    State(ids.DEPTS_OPEN_STORE, "data"),
    State(ids.ROOMS_OPEN_STORE, "data"),
    State(ids.BEDS_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(ids.TAB_SELECTOR, "value"),
    # background=True,
    # prevent_initial_call=True,
)
def _prepare_cyto_elements_campus(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    selected_dept: str,
    selected_tab: str,
) -> (list[dict], list[dict]):
    """
    Build the element list from pts/beds/rooms/depts for the map
    """
    elements = _make_elements(census, depts, rooms, beds, selected_dept, selected_tab)
    return elements


@callback(
    Output(ids.CYTO_WARD_CYTO, "elements"),
    State(ids.CENSUS_STORE, "data"),
    State(ids.DEPTS_OPEN_STORE, "data"),
    State(ids.ROOMS_OPEN_STORE, "data"),
    State(ids.BEDS_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(ids.TAB_SELECTOR, "value"),
    # background=True,
    # prevent_initial_call=True,
)
def _prepare_cyto_elements_ward(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    selected_dept: str,
    selected_tab: str,
) -> (list[dict], list[dict]):
    """
    Build the element list from pts/beds/rooms/depts for the map
    """
    elements = _make_elements(census, depts, rooms, beds, selected_dept, selected_tab)
    return elements


@callback(
    Output(ids.DEBUG_NODE_INSPECTOR, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
    prevent_initial_callback=True,
)
def tap_debug_inspector(data: dict) -> str:
    if data:
        # remove the style part of tapNode for readabilty
        data.pop("style", None)
    return json.dumps(data, indent=4)
