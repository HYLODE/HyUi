"""
Read and merge bed level data from Epic and EMAP
"""
import pandas as pd

from initialise import DEPARTMENTS, VIRTUAL_BEDS, VIRTUAL_ROOMS
from initialise.db import caboodle_engine, star_engine


def _star_locations() -> pd.DataFrame:
    # noinspection SqlResolve
    return pd.read_sql(
        """
    SELECT
        lo.location_id,
        lo.location_string AS location,
        SPLIT_PART(lo.location_string, '^', 1) AS hl7_department,
        SPLIT_PART(lo.location_string, '^', 2) AS hl7_room,
        SPLIT_PART(lo.location_string, '^', 3) AS hl7_bed,
        lo.department_id,
        lo.room_id,
        lo.bed_id,
        dept.name AS department,
        dept.speciality,
        room.name room
    FROM star.location lo
    INNER JOIN star.department dept ON lo.department_id = dept.department_id
    INNER JOIN star.room ON lo.room_id = room.room_id
    """,
        star_engine(),
    )


def _caboodle_departments() -> pd.DataFrame:
    # noinspection SqlResolve
    return pd.read_sql(
        """SELECT
            --DepartmentKey AS department_key,
            --BedEpicId AS bed_epic_id,
            Name AS name,
            DepartmentName AS department_name,
            RoomName AS room_name,
            BedName AS bed_name,
            --BedInCensus AS bed_in_census,
            IsRoom AS is_room,
            IsCareArea AS is_care_area,
            DepartmentExternalName AS department_external_name,
            DepartmentSpecialty AS department_speciality,
            DepartmentType AS department_type,
            DepartmentServiceGrouper AS department_service_grouper,
            DepartmentLevelOfCareGrouper AS department_level_of_care_grouper,
            LocationName AS location_name,
            ParentLocationName AS parent_location_name,
            _CreationInstant AS creation_instant,
            _LastUpdatedInstant AS last_updated_instant
        FROM dbo.DepartmentDim
        WHERE IsBed = 1
        AND Name <> 'Wait'
        AND DepartmentType <> 'OR'
        ORDER BY DepartmentName, RoomName, BedName, _CreationInstant""",
        caboodle_engine(),
    )


def _merge_star_and_caboodle_beds(
    star_locations_df: pd.DataFrame,
    caboodle_departments_df: pd.DataFrame,
) -> pd.DataFrame:
    star_locations_df = star_locations_df.copy()
    caboodle_departments_df = caboodle_departments_df.copy()

    # Limit departments to those we are interested in.
    star_locations_df = star_locations_df.loc[
        star_locations_df["department"].isin(DEPARTMENTS), :
    ]
    caboodle_departments_df = caboodle_departments_df.loc[
        caboodle_departments_df["department_name"].isin(DEPARTMENTS), :
    ]

    # Remove virtual rooms and beds.
    star_locations_df = star_locations_df.loc[
        ~star_locations_df["hl7_room"].isin(VIRTUAL_ROOMS), :
    ]
    star_locations_df = star_locations_df.loc[
        ~star_locations_df["hl7_bed"].isin(VIRTUAL_BEDS), :
    ]

    # Make key to merge and force to lower etc.
    star_locations_df["merge_key"] = star_locations_df.agg(
        lambda x: (
            # x["speciality"],
            x["department"],
            x["room"],
            x["hl7_bed"].lower(),
        ),
        axis=1,
    )

    # Still left with dups so now choose the most recent
    caboodle_departments_df.sort_values(
        by=["department_name", "room_name", "bed_name", "creation_instant"],
        inplace=True,
    )
    caboodle_departments_df.drop_duplicates(
        subset=["department_name", "room_name", "bed_name"], keep="last", inplace=True
    )

    # Make key to merge and force to lower etc
    caboodle_departments_df["merge_key"] = caboodle_departments_df.agg(
        lambda x: (
            # x["department_speciality"],
            x["department_name"],
            x["room_name"],
            x["name"].lower(),
        ),
        axis=1,
    )

    return star_locations_df.merge(
        caboodle_departments_df,
        how="inner",
        on="merge_key",
    ).drop(
        [
            "merge_key",
            "last_updated_instant",
            "creation_instant",
            "name",
            "room_name",
            "bed_name",
        ],
        axis="columns",
    )


def _fetch_beds() -> pd.DataFrame:
    star_locations_df = _star_locations()
    caboodle_departments_df = _caboodle_departments()
    beds_df = _merge_star_and_caboodle_beds(star_locations_df, caboodle_departments_df)
    return beds_df
