from typing import Any
import dash
import dash_mantine_components as dmc
import json
import pandas as pd
import requests
from dash import Input, Output, State, callback
from datetime import datetime
from types import SimpleNamespace
from typing import Tuple

from models.census import CensusRow
from web.config import get_settings
from web.pages.sitrep import CAMPUSES, ids
from web.stores import ids as store_ids
from web.style import colors

DEBUG = True


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
    return [i.get("department", {}) for i in depts_open]


@callback(
    Output(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(store_ids.ROOM_STORE, "data"),
)
def _store_rooms(
    depts: list[dict],
    rooms: list[dict],
) -> list[dict]:
    """Need a list of rooms for this building"""
    dfdepts = pd.DataFrame.from_records(depts)
    dfdepts = dfdepts[["department", "hl7_department"]]
    dfrooms = pd.DataFrame.from_records(rooms)
    # default inner join drops rooms not in the selected departments
    dfrooms = dfrooms.merge(dfdepts, on="department")
    # drop closed rooms
    dfrooms = dfrooms.loc[~dfrooms["closed"], :]

    return dfrooms.to_dict(orient="records")  # type: ignore


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.ROOMS_OPEN_STORE, "data"),
    Input(store_ids.BEDS_STORE, "data"),
)
def _store_beds(
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
) -> list[dict]:
    """
    Return a list of beds using the local filtered versions of depts/rooms
    - generate the floor_index from the bed_number to permit appropriate sorting
    """

    bedsdf = pd.DataFrame.from_records(beds)
    dfdepts = pd.DataFrame.from_records(depts)
    dfrooms = pd.DataFrame.from_records(rooms)

    dfdepts = dfdepts[["department", "floor_order"]]

    # drop beds where rooms are closed
    # look for bays where all beds are closed
    dft = bedsdf.groupby("hl7_room")["closed"].all()
    dft = pd.DataFrame(dft).reset_index()
    dft.rename(columns={"closed": "closed_all_beds"}, inplace=True)
    dfrooms = dfrooms.merge(dft, on="hl7_room")

    # now close a room if any of the following are true
    dfrooms["closed"] = dfrooms["closed"] | dfrooms["closed_all_beds"]
    dfrooms.drop(columns=["closed_all_beds"], inplace=True)
    # drop closed rooms
    dfrooms = dfrooms.loc[~dfrooms["closed"], :]
    dfrooms = dfrooms[["hl7_room", "is_sideroom"]]

    # inner join to drop rooms without beds
    bedsdf = bedsdf.merge(dfrooms, on="hl7_room", how="inner")
    # inner join to drop closed_perm_01
    bedsdf = bedsdf.merge(dfdepts, on="department", how="inner")

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
    background=True,
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
    [
        Output(ids.DEPT_SELECTOR, "data"),
        Output(ids.DEPT_SELECTOR, "value"),
    ],
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
)
def _dept_select_control(depts: list[str], campus: str) -> Tuple[list[str], str]:
    """Populate select input with data (dept name) and default value"""
    default = [i.get("default_dept", "") for i in CAMPUSES if i.get("value") == campus][
        0
    ]
    return depts, default


def _make_elements(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    selected_dept: str | None,
    ward_only: bool,
) -> list[dict]:
    """
    Logic to create elements for cyto map

    Args:
        census: list of bed status objects with occupancy (census)
        depts: list of dept objects
        rooms: list of room objects
        beds: list of bed objects (from baserow)
        selected_dept: name of dept or None if show all
        ward_only: True if ward_only not campus; default False

    Returns:
        list of elements for cytoscape map
    """

    # Start with an empty list of elements to populate
    elements = list()

    # show either rooms or department as parent but not both
    show_rooms = True if ward_only else False
    show_depts = not show_rooms
    bed_parent = "hl7_room" if show_rooms else "department"
    # define the 'height' of the map
    y_index_max = max([bed.get("floor_y_index", -1) for bed in beds])
    census_lookup = {i.get("location_string"): i for i in census}

    # create beds
    for bed in beds:
        department = bed.get("department")
        # skip bed if a ward only map and wrong dept
        if ward_only and department != selected_dept:
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
            census=census_lookup.get(location_string, {}),
            closed=bed.get("closed"),
            blocked=bed.get("blocked"),
            occupied=census_lookup.get(location_string, {}).get("occupied", "False"),
        )
        position = dict(
            x=bed.get("floor_x_index", -1) * 40,
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
            if department != selected_dept:
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
    Output(ids.CYTO_CAMPUS, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.BEDS_STORE, "data"),
    prevent_initial_call=True,
)
def _prepare_cyto_elements_campus(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
) -> list[dict]:
    """
    Build the element list from pts/beds/rooms/depts for the map
    """
    elements = _make_elements(
        census, depts, rooms, beds, selected_dept=None, ward_only=False
    )
    return elements


@callback(
    Output(ids.CYTO_WARD, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.BEDS_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    prevent_initial_call=True,
)
def _prepare_cyto_elements_ward(
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    dept: str,
) -> list[dict]:
    """
    Build the element list from pts/beds/rooms/depts for the map
    """
    elements = _make_elements(
        census, depts, rooms, beds, selected_dept=dept, ward_only=True
    )
    return elements


def _format_tap_node_data(data: dict | None) -> str:
    if data:
        # remove the style part of tapNode for readabilty
        data.pop("style", None)
    return json.dumps(data, indent=4)


@callback(
    [
        Output(ids.DEBUG_NODE_INSPECTOR_CAMPUS, "children"),
        Output(ids.INSPECTOR_CAMPUS, "opened"),
    ],
    Input(ids.CYTO_CAMPUS, "tapNode"),
    State(ids.INSPECTOR_CAMPUS, "opened"),
    prevent_initial_callback=True,
)
def tap_debug_inspector_campus(data: dict, opened: str) -> Tuple[str, bool]:
    if not DEBUG:
        return dash.no_update, False
    if not data:
        return _format_tap_node_data(data), False
    else:
        return _format_tap_node_data(data), not opened


def format_census(census: dict) -> dict:
    """Given a census object return a suitably formatted dictionary"""
    mrn = census.get("mrn", "")
    encounter = str(census.get("encounter", ""))
    lastname = census.get("lastname", "").upper()
    firstname = census.get("firstname", "").title()
    initials = f"{census.get('firstname', '?')[0]}" f"{census.get('lastname', '?')[0]}"
    date_of_birth = census.get("date_of_birth", "1900-01-01")  # default dob
    dob = datetime.fromisoformat(date_of_birth)
    dob_fshort = datetime.strftime(dob, "%d-%m-%Y")
    dob_flong = datetime.strftime(dob, "%d %b %Y")
    age = int((datetime.utcnow() - dob).days / 365.25)
    sex = census.get("sex")
    if sex is None:
        sex = ""
    else:
        sex = "M" if sex.lower() == "m" else "F"

    return dict(
        mrn=mrn,
        encounter=encounter,
        lastname=lastname,
        firstname=firstname,
        initials=initials,
        dob=dob,
        dob_fshort=dob_fshort,
        dob_flong=dob_flong,
        age=age,
        sex=sex,
        demographic_slug=f"{firstname} {lastname} | {age}{sex} | MRN {mrn}",
    )


def _create_accordion_item(control: Any, panel: Any) -> Any:
    return [dmc.AccordionControl(control), dmc.AccordionPanel(panel)]


@callback(
    [
        Output(ids.INSPECTOR_WARD, "opened"),
        Output(ids.DEBUG_NODE_INSPECTOR_WARD, "children"),
        Output(ids.INSPECTOR_WARD, "title"),
        Output(ids.MODAL_ACCORDION_PATIENT, "children"),
    ],
    Input(ids.CYTO_WARD, "tapNode"),
    State(ids.INSPECTOR_WARD, "opened"),
    prevent_initial_callback=True,
)
def tap_inspector_ward(node: dict, modal_opened: str) -> Tuple[bool, str, str, str]:
    """
    Populate the bed inspector modal
    Args:
        node:
        modal_opened:

    Returns:
        modal: open status (toggle)
        debug_inspection: json formattd string
        title: title of the modal built from patient data
        patient_content: to be viewed in the modal

    """
    if not node:
        return False, dash.no_update, "", ""

    data = node.get("data", {})
    if data.get("entity") != "bed":
        return False, dash.no_update, "", ""

    occupied = data.get("occupied")

    bed = data.get("bed")
    bed_prefix = "Sideroom" if bed.get("sideroom") else "Bed"

    modal_title = f"{bed_prefix} {bed.get('bed_number')}  " f"({bed.get('department')})"
    accordion_pt_content = _create_accordion_item("🔬 Unoccupied", "")

    if occupied:
        census = data.get("census")
        cfmt = SimpleNamespace(**format_census(census))
        accordion_pt_content = _create_accordion_item(
            f"🔬 {cfmt.demographic_slug}", "🚧 Patient details under construction 🚧"
        )

    return (
        not modal_opened,
        _format_tap_node_data(node),
        modal_title,
        accordion_pt_content,
    )


@callback(
    Output(ids.PROGRESS_CAMPUS, "sections"),
    Input(ids.CYTO_CAMPUS, "elements"),
    prevent_initial_call=True,
)
def progress_bar_campus(elements: list[dict]) -> list[dict]:
    beds = [
        ele.get("data", {})
        for ele in elements
        if ele.get("data", {}).get("entity") == "bed"
    ]

    # TODO: replace with total capacity from department sum
    N = len(beds)
    occupied = len([i for i in beds if i.get("occupied")])
    blocked = len([i for i in beds if i.get("blocked")])
    empty = N - occupied - blocked
    empty_p = empty / N

    # Adjust colors and labels based on size
    blocked_label = "" if blocked / N < 0.1 else "Blocked"
    empty_label = "" if empty_p < 0.1 else "Empty"
    if empty_p < 0.05:
        empty_colour = colors.red
    elif empty_p < 0.1:
        empty_colour = colors.yellow
    else:
        empty_colour = colors.green

    return [
        dict(
            value=occupied / N * 100,
            color=colors.teal,
            label="Occupied",
            tooltip=f"{occupied} beds",
        ),
        dict(
            value=blocked / N * 100,
            color=colors.gray,
            label=blocked_label,
            tooltip=f"{blocked} beds",
        ),
        dict(
            value=empty / N * 100,
            color=empty_colour,
            label=empty_label,
            tooltip=f"{empty} beds",
        ),
    ]
