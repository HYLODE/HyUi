import pandas as pd
import warnings
from dash import Input, Output, callback
from datetime import datetime
from typing import Tuple

from models.census import CensusRow
from web.config import get_settings
from web.pages.perrt import CAMPUSES, ids
from web.stores import ids as store_ids
from web.celery_tasks import requests_try_cache

DEBUG = True


@callback(
    Output(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.DEPT_STORE, "data"),
)
def _store_depts(campus: str, depts: list[dict]) -> list[dict]:
    """Need a list of departments for this building"""
    try:
        these_depts = [dept for dept in depts if dept.get("location_name") == campus]
    except TypeError as e:
        print(e)
        warnings.warn(f"No departments found at {campus} campus")
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
    campus_short_name = next(
        i.get("label") for i in CAMPUSES if i.get("value") == campus
    )

    # Drop in replacement for requests.get that uses the redis cache
    # response = requests.get(
    #     f"{get_settings().api_url}/census/campus/",
    #     params={"campuses": campus_short_name},
    # )
    url = f"{get_settings().api_url}/census/campus/"
    params = {"campuses": campus_short_name}
    data = requests_try_cache(url, params=params)

    res = [CensusRow.parse_obj(row).dict() for row in data]
    res = [row for row in res if row.get("department") in depts_open_names]
    return res


@callback(
    Output(ids.NEWS_STORE, "data"),
    Input(ids.CENSUS_STORE, "data"),
    prevent_initial_callback=True,
)
def _store_news(census: list[dict]) -> list[dict]:
    """
    Use the census store to provide the CSNs to query additional data
    Args:
        census:

    Returns:
        NEWS score for each patient in the CENSUS
    """
    csn_list = [i.get("encounter") for i in census if i.get("occupied")]  # type: ignore

    url = f"{get_settings().api_url}/perrt/vitals/wide"
    params = {"encounter_ids": csn_list}
    data = requests_try_cache(url, params=params)

    newsdf = pd.DataFrame.from_records(data)
    # TODO: simpplify: you just want the most recent and highest NEWS score
    #  and its timestamp

    news: list[dict] = newsdf.to_dict(orient="records")
    return news


@callback(
    Output(ids.PREDICTIONS_STORE, "data"),
    Input(ids.CENSUS_STORE, "data"),
)
def _store_predictions(census: list[dict]) -> dict:
    """
    Use the census store to provide the CSNs to query admission prediction data
    Args:
        census:

    Returns:
        Admission prediction data for each patient in the CENSUS,if it exists,
        NULL otherwise
    """
    hv_id_list = [i.get("ovl_hv_id") for i in census if i.get("occupied")]
    url = f"{get_settings().api_url}/perrt/icu_admission_prediction"
    params = {"hospital_visit_ids": hv_id_list}  # type: ignore
    predictions = requests_try_cache(url, params=params)

    return predictions  # type: ignore


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


def _make_elements(  # noqa: C901
    census: list[dict],
    depts: list[dict],
    beds: list[dict],
    news: list[dict],
    predictions: dict,
) -> list[dict]:
    """
    Logic to create elements for cyto map

    Args:
        census: list of bed status objects with occupancy (census)
        depts: list of dept objects
        beds: list of bed objects (from baserow)

    Returns:
        list of elements for cytoscape map
    """

    # Start with an empty list of elements to populate
    elements = list()

    # define the 'height' of the map
    y_index_max = max([bed.get("floor_y_index", -1) for bed in beds])
    census_lookup = {i.get("location_string"): i for i in census}
    news_lookup = {i.get("encounter"): i for i in news}

    # create beds
    for bed in beds:
        department = bed.get("department")
        location_string = bed.get("location_string")

        occupied = census_lookup.get(location_string, {}).get("occupied", False)
        encounter = census_lookup.get(location_string, {}).get("encounter", "")
        hospital_visit_id = census_lookup.get(location_string, {}).get(
            "ovl_hv_id", None
        )
        news_wide: dict = news_lookup.get(encounter, {})  # type: ignore

        # Hospital_visit_ids are integers, but the dictionary uses strings for keys.
        # Lookup using a string to be safe
        # Don't get the prediction if the bed isn't occupied
        admission_prediction = (
            predictions.get(str(hospital_visit_id), None) if occupied else None
        )

        def _max_news_wide(row: dict) -> int:
            if not row:
                return -1
            scale_1_max = row.get("news_scale_1_max", -1)
            scale_2_max = row.get("news_scale_2_max", -1)
            max_news: int = max(
                i for i in [-1, scale_1_max, scale_2_max] if i is not None
            )

            return max_news

        data = dict(
            id=location_string,
            bed_number=bed.get("bed_number"),
            bed_index=bed.get("bed_index"),
            department=department,
            floor=bed.get("floor"),
            entity="bed",
            parent=bed.get("department"),
            bed=bed,
            census=census_lookup.get(location_string, {}),
            closed=bed.get("closed"),
            blocked=bed.get("blocked"),
            occupied=occupied,
            encounter=encounter,
            news=news_wide,
            news_max=_max_news_wide(news_wide),
            admission_prediction=admission_prediction,
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

    for dept in depts:
        dept_name = dept.get("department")
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
                selected=False,
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
    Input(ids.BEDS_STORE, "data"),
    Input(ids.NEWS_STORE, "data"),
    Input(ids.PREDICTIONS_STORE, "data"),
    prevent_initial_call=True,
)
def _prepare_cyto_elements_campus(
    census: list[dict],
    depts: list[dict],
    beds: list[dict],
    news: list[dict],
    predictions: dict,
) -> list[dict]:
    """
    Build the element list from pts/beds/rooms/depts for the map
    """
    elements = _make_elements(census, depts, beds, news, predictions)
    return elements


def format_census(census: dict) -> dict:
    """Given a census object return a suitably formatted dictionary"""
    mrn = census.get("mrn", "")
    encounter = str(census.get("encounter", ""))
    lastname = census.get("lastname", "").upper()
    firstname = census.get("firstname", "").title()
    initials = (
        f"{census.get('firstname', '?')[0]}"
        f""
        f""
        f""
        f"{census.get('lastname', '?')[0]}"
    )
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
