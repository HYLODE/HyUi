import pandas as pd
from dash import Input, Output, callback
from loguru import logger

from web import SITREP_DEPT2WARD_MAPPING, ids as store_ids
from web.logger import logger_timeit
from web.pages.sitrep import ids


@callback(
    Output(ids.DEPTS_OPEN_STORE, "data"),
    Input(ids.DEPT_GROUPER, "value"),
    Input(store_ids.DEPT_STORE, "data"),
)
@logger_timeit(level="DEBUG")
def _store_depts(dept_grouper: str, depts: list[dict]) -> list[dict]:
    """Need a list of departments for ALL_ICUS or this campus"""
    logger.info("just testing")
    if dept_grouper == "ALL_ICUS":
        icus = SITREP_DEPT2WARD_MAPPING.keys()
        these_depts = [dept for dept in depts if dept.get("department") in icus]
    else:
        try:
            these_depts = [
                dept for dept in depts if dept.get("location_name") == dept_grouper
            ]
        except TypeError as e:
            logger.warning(f"No departments found at {dept_grouper} campus")
            logger.exception(e)
            these_depts = []
    return these_depts


@callback(
    Output(ids.DEPTS_OPEN_STORE_NAMES, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
)
def _dept_open_store_names(depts_open: list[dict]) -> list[str]:
    """
    Return a list of department names from a list of dictionaries
    """
    return [i.get("department", {}) for i in depts_open]


@callback(
    Output(ids.ROOMS_OPEN_STORE, "data"),
    Input(ids.DEPTS_OPEN_STORE, "data"),
    Input(store_ids.ROOM_STORE, "data"),
)
@logger_timeit(level="DEBUG")
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
@logger_timeit(level="DEBUG")
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
