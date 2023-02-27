import dash
import pandas as pd
import requests
import warnings
from dash import Input, Output, State, callback, callback_context
from datetime import datetime
from typing import Any, Tuple

from models.census import CensusRow
from web import SITREP_DEPT2WARD_MAPPING
from web.config import get_settings
from web.pages.sitrep import CAMPUSES, ids
from web.stores import ids as store_ids
from web.utils import Timer

# =============================================================================
DEBUG = True
# =============================================================================


@callback(
    Output(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.DEPT_GROUPER, "value"),
    Input(store_ids.DEPT_STORE, "data"),
)
def _store_depts(dept_grouper: str, depts: list[dict]) -> list[dict]:
    """Need a list of departments for ALL_ICUS or this campus"""
    if dept_grouper == "ALL_ICUS":
        icus = SITREP_DEPT2WARD_MAPPING.keys()
        these_depts = [dept for dept in depts if dept.get("department") in icus]
    else:
        try:
            these_depts = [
                dept for dept in depts if dept.get("location_name") == dept_grouper
            ]
        except TypeError as e:
            print(e)
            warnings.warn(f"No departments found at {dept_grouper} campus")
            these_depts = []
    return these_depts


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
    # bedsdf = bedsdf[~bedsdf["closed"]]

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
    Input(ids.DEPT_GROUPER, "value"),
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
)
def _store_census(
    dept_grouper: str,
    depts_open_names: list[str],
) -> list[dict]:
    """
    Store CensusRow as list of dictionaries after filtering out closed
    departments for that building
    Args:
        dept_grouper: one of UCH/WMS/GWB/NHNN
        depts_open_names: list of departments that are open

    Returns:
        Filtered list of CensusRow dictionaries

    """
    if dept_grouper == "ALL_ICUS":
        response = requests.get(
            f"{get_settings().api_url}/census/",
            params={"departments": SITREP_DEPT2WARD_MAPPING.keys()},
        )
    else:
        campus_short_name = next(
            i.get("label") for i in CAMPUSES if i.get("value") == dept_grouper
        )

        response = requests.get(
            f"{get_settings().api_url}/census/campus/",
            params={"campuses": campus_short_name},
        )

    res = [CensusRow.parse_obj(row).dict() for row in response.json()]
    res = [row for row in res if row.get("department") in depts_open_names]
    return res


@callback(
    Output(ids.SITREP_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(store_ids.SITREP_STORE, "data"),
    prevent_initial_callback=True,
    background=True,
)
def _store_sitrep(dept: str, sitreps: dict) -> Any:
    """
    Args:
        dept: the department
        sitreps: dictionary of sitreps

    Returns:
        additonal patient level data

    """
    # ward2dept = {v:k for k,v in SITREP_DEPT2WARD_MAPPING.items()}
    # department = ward2dept.get(dept)
    ward = SITREP_DEPT2WARD_MAPPING.get(dept)
    if not ward:
        warnings.warn(f"No sitrep data available for {ward}")
        return [{}]
    return sitreps[ward]


@callback(
    Output(ids.HYMIND_DC_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(store_ids.HYMIND_ICU_DC_STORE, "data"),
    prevent_initial_callback=True,
    background=True,
)
def _store_hymind_dc(dept: str, hymind_dcs: dict) -> Any:
    """
    Args:
        dept: the department
        hymind_dcs: dictionary of hymind predictions per unit

    Returns:
        additonal individual level dc predictions for that ward

    """
    ward = SITREP_DEPT2WARD_MAPPING.get(dept)
    if not ward:
        warnings.warn(f"No HyMind Discharge predictions available for {ward}")
        return [{}]
    return hymind_dcs[ward]


@Timer(text="Discharge updates: Elapsed time: {:.3f} seconds")
def _get_discharge_updates(delta_hours: int = 48) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/baserow/discharge_status",
        params={"delta_hours": delta_hours},
    )
    if response.status_code == 200:
        return response.json()  # type: ignore
    else:
        warnings.warn("No data found for discharge statues (from Baserow " "store)")
        return [{}]


@callback(
    Output(ids.DISCHARGES_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
)
def store_discharge_status(dept: str) -> list[dict]:
    """
    Get discharge status
    Deduplicate to most recent only
    Refreshes on ward update
    """
    if not dept:
        return dash.no_update  # type: ignore
    discharges = _get_discharge_updates(delta_hours=36)
    if not discharges or not len(discharges):
        return dash.no_update  # type: ignore
    df = pd.DataFrame.from_records(discharges)
    try:
        df.sort_values(["csn", "modified_at"], ascending=[True, False], inplace=True)
        df.drop_duplicates(["csn"], inplace=True)
    except KeyError as e:
        print(e)
        warnings.warn("Unable to sort: is the dataframe empty?")
    return df.to_dict(orient="records")  # type: ignore


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
    try:
        discharge_lookup = {str(i.get("csn")): i for i in discharges}
    except TypeError as e:
        warnings.warn("Possible type error b/c no recent discharges")
        print(e)
        discharge_lookup = {}

    sitrep_lookup = {i.get("csn"): i for i in sitrep}
    hymind_lookup = {i.get("episode_slice_id"): i for i in hymind}
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
            hymind_dc=hymind_lookup.get(episode_slice_id, {}),
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
