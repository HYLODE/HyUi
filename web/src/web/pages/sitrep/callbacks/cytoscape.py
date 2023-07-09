import dash
from dash import Input, Output, State, callback, callback_context
from typing import Tuple, Any

from web.pages.sitrep import CAMPUSES, ids
from web import SITREP_DEPT2WARD_MAPPING

from web.logger import logger, logger_timeit

logger.info("Preparing cytoscape map")


@callback(
    [
        Output(ids.DEPT_SELECTOR, "data"),
        Output(ids.DEPT_SELECTOR, "value"),
    ],
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    Input(ids.DEPT_GROUPER, "value"),
)
def _dept_select_control(depts: list[Any], dept_grouper: str) -> Tuple[list[str], str]:
    """Populate select input with data (dept name) and default value"""
    if dept_grouper == "ALL_ICUS":
        default = "UCH T03 INTENSIVE CARE"
        depts = [
            {"value": k, "label": v} for k, v in list(SITREP_DEPT2WARD_MAPPING.items())
        ]
    else:
        default = [
            i.get("default_dept", "")
            for i in CAMPUSES
            if i.get("value") == dept_grouper
        ][0]
    return depts, default


def _make_elements(  # noqa: C901
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    sitrep: list[dict],
    hymind: list[dict],
    discharges: list[dict],
    selected_dept: str | None,
    ward_only: bool,
    preset_map_positions: bool = False,
) -> list[dict]:
    """
    Logic to create elements for cyto map

    Args:
        census: list of bed status objects with occupancy (census)
        depts: list of dept objects
        rooms: list of room objects
        beds: list of bed objects (from baserow)
        sitrep: list of sitrep statuses (from hylode)
        hymind: list of patient level discharge predictions
        discharges: list of discharge statuses (from baserow)
        selected_dept: name of dept or None if show all
        ward_only: True if ward_only not campus; default False
        preset_map_positions: default False

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

    # TODO: rebuild discharge_statuses table with encounter as string
    # TODO: fix naming (use 'encounter' in census and 'csn' in discharges)
    # convert csn to string since that's how encounter is stored in EMAP
    if discharges:
        discharge_lookup = {str(i.get("csn")): i for i in discharges}
    else:
        logger.warning("Discharges empty: no data available")
        discharge_lookup = {}

    if sitrep is not None:
        sitrep_lookup = {i.get("csn"): i for i in sitrep}
    else:
        logger.warning("Sitrep empty: no data available")
        sitrep_lookup = {}

    if hymind is not None:
        hymind_lookup = {i.get("episode_slice_id"): i for i in hymind}
    else:
        logger.warning("Hymind empty: no data available")
        hymind_lookup = {}

    preset_map_positions = (
        False
        if selected_dept not in SITREP_DEPT2WARD_MAPPING.keys()
        else preset_map_positions
    )

    # create beds
    for bed in beds:
        department = bed.get("department")
        # skip bed if a ward only map and wrong dept
        if ward_only and department != selected_dept:
            continue
        location_string = bed.get("location_string")

        occupied = census_lookup.get(location_string, {}).get("occupied", False)
        encounter = census_lookup.get(location_string, {}).get("encounter", "")
        discharge_status = discharge_lookup.get(encounter, {}).get("status", "")
        wim = sitrep_lookup.get(encounter, {}).get("wim_1", -1)
        episode_slice_id = sitrep_lookup.get(encounter, {}).get("episode_slice_id", -1)
        yhat_dc = hymind_lookup.get(episode_slice_id, {}).get("prediction_as_real", -1)

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
            occupied=occupied,
            encounter=encounter,
            dc_status=discharge_status,
            wim=wim,
            sitrep=sitrep_lookup.get(encounter, {}),
            yhat_dc=yhat_dc,
        )
        if preset_map_positions:
            position = dict(
                x=bed.get("xpos", 1) * 9,
                y=bed.get("ypos", 1) * 9,
            )
        else:
            position = dict(
                x=bed.get("floor_x_index", -1) * 40,
                y=(y_index_max - bed.get("floor_y_index", -1)) * 60,
            )
        elements.append(
            dict(
                data=data,
                position=position,
                grabbable=False,
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
                sideroom=room.get("is_sideroom"),
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
    # Sort elements by floor/dept/bed_number: NB: make a tuple for the sort
    # https://stackoverflow.com/a/33893264/992999
    elements = sorted(
        elements,
        key=lambda e: (
            e.get("data").get("entity", ""),  # type: ignore
            e.get("data").get("department", ""),  # type: ignore
            e.get("data").get("bed_number", ""),  # type: ignore
        ),
    )  # type: ignore
    return elements  # type: ignore


@callback(
    Output(ids.CYTO_CAMPUS, "elements"),
    Input(ids.CENSUS_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.BEDS_STORE, "data"),
    prevent_initial_call=True,
)
@logger_timeit()
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
        census,
        depts,
        rooms,
        beds,
        sitrep=[{}],
        hymind=[{}],
        discharges=[{}],
        selected_dept=None,
        ward_only=False,
    )
    return elements


@callback(
    Output(ids.CYTO_WARD, "elements"),
    [
        State(ids.CYTO_WARD, "elements"),
        Input(ids.CENSUS_STORE, "data"),
        Input(ids.DEPTS_OPEN_STORE, "data"),
        Input(ids.ROOMS_OPEN_STORE, "data"),
        Input(ids.BEDS_STORE, "data"),
        Input(ids.SITREP_STORE, "data"),
        Input(ids.HYMIND_DC_STORE, "data"),
        Input(ids.DISCHARGES_STORE, "data"),
        Input(ids.DEPT_SELECTOR, "value"),
        Input(ids.ACC_BED_SUBMIT_STORE, "data"),
        State(ids.DEPT_GROUPER, "value"),
    ],
    prevent_initial_call=True,
)
@logger_timeit()
def _prepare_cyto_elements_ward(
    elements: list[dict],
    census: list[dict],
    depts: list[dict],
    rooms: list[dict],
    beds: list[dict],
    sitrep: list[dict],
    hymind: list[dict],
    discharges: list[dict],
    dept: str,
    bed_submit_store: dict,
    dept_grouper: str,
) -> list[dict]:
    """
    Build the element list from pts/beds/rooms/depts for the map
    Use the dept_grouper == ALL_ICUs to trigger the switch to using
    positions for preset layout
    """
    if callback_context.triggered_id != ids.ACC_BED_SUBMIT_STORE:
        preset_map_positions = True if dept_grouper == "ALL_ICUS" else False
        elements = _make_elements(
            census,
            depts,
            rooms,
            beds,
            sitrep,
            hymind,
            discharges,
            selected_dept=dept,
            ward_only=True,
            preset_map_positions=preset_map_positions,
        )
    elif callback_context.triggered_id == ids.ACC_BED_SUBMIT_STORE:
        node_id = bed_submit_store.get("id")
        for ele in elements:
            if ele.get("data", {}).get("id") != node_id:
                continue
            data = ele.get("data")  # type: ignore
            data.update(dc_status=bed_submit_store.get("status"))  # type: ignore
            break
    else:
        return dash.no_update  # type: ignore

    return elements  # type: ignore
