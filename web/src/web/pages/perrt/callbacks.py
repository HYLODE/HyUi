import datetime

from dash import Input, Output, callback, dcc

from models.census import CensusRow
from models.perrt import EmapConsults, EmapCpr, EmapVitalsWide
from web.census import get_census
from web.convert import to_data_frame
from web.hospital import departments_by_building
from web.pages.perrt import (
    BPID,
    CENSUS_KEEP_COLS,
    CPR_COLS,
    PERRT_CONSULTS_COLS,
    PERRT_VITALS_WIDE,
)
from web.perrt import get_cpr_status, get_perrt_consults, get_perrt_wide
from web.utils import time_since


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
    # TODO: should remove closed departments from the list defer until cache
    #  works since the query is slow
    default_value = [departments[0]]

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
    # return just the most recent CPR status per encounter
    df_cpr = df_cpr.sort_values(
        ["encounter", "status_change_datetime"], ascending=False
    ).drop_duplicates("encounter")
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

    # merge on NEWS
    horizon_dt = datetime.datetime.now() - datetime.timedelta(hours=6)
    perrt_vitals_wide = get_perrt_wide(encounter_ids, horizon_dt)
    df_vw = to_data_frame(perrt_vitals_wide, EmapVitalsWide)
    df_vw = df_vw[PERRT_VITALS_WIDE.keys()]
    df_vw["news_max"] = df_vw[["news_scale_1_max", "news_scale_2_max"]].max(axis=1)
    df_vw = df_vw[["encounter", "news_max"]]
    df = df.merge(df_vw, how="left", on="encounter", suffixes=(None, "_news"))

    df["bed_label"] = df["location_string"].str.split("^", expand=True)[2]
    # FIXME: 2022-12-13 LoS not displaying live
    df["los"] = time_since(df["hv_admission_dt"], units="D")
    df["age"] = time_since(df["date_of_birth"], units="Y")
    df["name"] = df.apply(
        lambda row: f"{row.lastname.upper()}, {row.firstname.title()}", axis=1
    )

    data = df.to_dict("records")
    return data  # type: ignore
