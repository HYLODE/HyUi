import numpy as np
import pandas as pd
from dash import Input, Output, callback, dcc

import datetime
from web.perrt import get_cpr_status, get_perrt_consults
from models.perrt import EmapCpr, EmapConsults
from models.census import CensusRow
from web.census import get_census
from web.convert import to_data_frame
from web.hospital import departments_by_building
from web.pages.perrt import (
    BPID,
    CENSUS_KEEP_COLS,
    CPR_COLS,
    PERRT_CONSULTS_COLS,
)


@callback(
    Output(f"{BPID}dept_dropdown_div", "children"),
    Input(f"{BPID}building_radio", "value"),
)
def gen_dept_dropdown(building: str):
    """
    Dynamically build department picker list

    :param      building:  The building
    :type       building:  str

    :returns:   { description_of_the_return_value }
    :rtype:     list
    """

    departments = departments_by_building(building)
    # TODO: should remove closed departments from the list defer until cache works since the query is slow
    default_value = departments

    return dcc.Dropdown(
        id=f"{BPID}dept_dropdown",
        value=default_value,
        options=[{"label": v, "value": v} for v in departments],
        placeholder="Choose which department(s)",
        multi=True,
    )


@callback(
    Output(f"{BPID}census_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    Input(f"{BPID}dept_dropdown", "value"),
    prevent_initial_call=True,
)
def store_census(n_intervals: int, departments: list[str]):
    """
    Returns current patients in selected departments
    """

    census = get_census(departments)
    df = to_data_frame(census, CensusRow)
    df = df[CENSUS_KEEP_COLS]
    # Scrub ghosts using the occupied mask.
    df = df[df["occupied"]]
    encounter_ids = df["encounter"]

    # merge CPR
    cpr = get_cpr_status(encounter_ids)
    df_cpr = to_data_frame(cpr, EmapCpr)
    df_cpr = df_cpr[CPR_COLS.keys()]
    df = df.merge(df_cpr, how="left", on="encounter", suffixes=(None, "_cpr"))
    df.rename(columns={"name": "name_cpr"}, inplace=True)

    # perrt consults in the last 7 days
    horizon_dt = datetime.datetime.now() - datetime.timedelta(days=7)
    perrt_consults = get_perrt_consults(encounter_ids, horizon_dt)
    df_pc = to_data_frame(perrt_consults, EmapConsults)
    df_pc = df_pc[PERRT_CONSULTS_COLS.keys()]
    # return just the most recent consult per encounter
    df_pc = df_pc.sort_values(
        ["encounter", "status_change_datetime"], ascending=False
    ).drop_duplicates("encounter")
    df = df.merge(df_pc, how="left", on="encounter", suffixes=(None, "_consults"))
    df.rename(columns={"name": "name_consults"}, inplace=True)

    # TODO: @next 2022-12-12t18:31:37 merge on NEWS

    # TODO: @next add hospital admission datetime into census model so can
    #  calc LoS

    # TODO: @resume 2022-12-12t18:30:27 factor out these functions
    df["age"] = (
        pd.Timestamp.now() - df["date_of_birth"].apply(pd.to_datetime)
    ) / np.timedelta64(1, "Y")
    df["name"] = df.apply(
        lambda row: f"{row.lastname.upper()}, {row.firstname.title()}", axis=1
    )

    data = df.to_dict("records")
    return data  # type: ignore
