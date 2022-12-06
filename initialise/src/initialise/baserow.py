import json
import logging
from typing import cast

import pandas as pd
import requests

from initialise.config import get_baserow_settings, BaserowSettings
from initialise.db import star_engine, caboodle_engine


DEPARTMENTS = (
    "UCH T01 ACUTE MEDICAL",  # 86
    "UCH T01 ENHANCED CARE",  # 20
    "UCH T03 INTENSIVE CARE",  # 37
    "UCH T06 HEAD (T06H)",  # 27
    "UCH T06 CENTRAL (T06C)",  # 25
    "UCH T06 SOUTH PACU",  # 22
    "UCH T06 GYNAE (T06G)",  # 18
    "UCH T07 NORTH (T07N)",  # 45
    "UCH T07 CV SURGE",  # 37
    "UCH T07 SOUTH",  # 33
    "UCH T07 SOUTH (T07S)",  # 23
    "UCH T07 HDRU",  # 20
    "UCH T08 NORTH (T08N)",  # 28
    "UCH T08 SOUTH (T08S)",  # 25
    "UCH T08S ARCU",  # 6
    "UCH T09 SOUTH (T09S)",  # 34
    "UCH T09 NORTH (T09N)",  # 32
    "UCH T09 CENTRAL (T09C)",  # 25
    "UCH T10 SOUTH (T10S)",  # 34
    "UCH T10 NORTH (T10N)",  # 32
    "UCH T10 MED (T10M)",  # 16
    "UCH T11 SOUTH (T11S)",  # 27
    "UCH T11 NORTH (T11N)",  # 25
    "UCH T11 EAST (T11E)",  # 16
    "UCH T11 NORTH (T11NO)",  # 8
    "UCH T12 SOUTH (T12S)",  # 32
    "UCH T12 NORTH (T12N)",  # 23
    "UCH T13 SOUTH (T13S)",  # 31
    "UCH T13 NORTH ONCOLOGY",  # 26
    "UCH T13 NORTH (T13N)",  # 26
    "UCH T14 NORTH TRAUMA",  # 28
    "UCH T14 NORTH (T14N)",  # 28
    "UCH T14 SOUTH ASU",  # 22
    "UCH T14 SOUTH (T14S)",  # 17
    "UCH T15 SOUTH DECANT",  # 21
    "UCH T15 SOUTH (T15S)",  # 21
    "UCH T15 NORTH (T15N)",  # 16
    "UCH T15 NORTH DECANT",  # 15
    "UCH T16 NORTH (T16N)",  # 19
    "UCH T16 SOUTH (T16S)",  # 18
    "UCH T16 SOUTH WINTER",  # 17
    "GWB L01 ELECTIVE SURG",  # 37
    "GWB L01 CRITICAL CARE",  # 12
    "GWB L02 NORTH (L02N)",  # 19
    "GWB L02 EAST (L02E)",  # 19
    "GWB L03 NORTH (L03N)",  # 19
    "GWB L03 EAST (L03E)",  # 19
    "GWB L04 NORTH (L04N)",  # 20
    "GWB L04 EAST (L04E)",  # 17
    "WMS W04 WARD",  # 28
    "WMS W03 WARD",  # 27
    "WMS W02 SHORT STAY",  # 20
    "WMS W01 CRITICAL CARE",  # 11
)

VIRTUAL_ROOMS = (
    "WAITING",
    "CHAIRS",
    "POOL ROOM",
    "DENTAL CHAIRS",
    "ADULT TRIAGE",
    "LOUNGE",
    "ARRIVED",
    "DISCHARGE",
    "WAIT",
    "VIRTUAL GI",
    "VIRTUAL T&O",
    "POOL",
    "CLINIC",
    "OTF",
    "L&D PACU",
    "MAJAX P03 RECOVERY",
    "VIRTUAL UROLOGY",
    "REVIEW AND BLOOD TEST BAY",
    "PHYSIO",
    "PROC",
    "IR",
    "LITHOTRIPSY ROOM",
    "IN TREATMENT",
    "CORRIDOR",
    "LEAVE OF ABSCENCE",
    "KITCHEN",
    "HOME",
    "WAITING ROOM",
    "VIRTUAL ENDOSCOPY",
    "DAYCASE",
    "MAJAX P01 SURGICAL RECEPTION",
    "MAJAX P02 ENDOSCOPY",
)

VIRTUAL_BEDS = (
    "POOL",
    "NONE",
    "ENDO",
    "IMG",
    "OUT PG",
    "IR",
    "WAIT",
    "IR",
    "THR",
    "WAITING",
    "OTF",
    "ARRIVED",
    "CHAIR",
    "VIRTUAL",
    "-",
    "PLASTER ROOM",
    "TREATMENT ROOM",
    "OPHTHALMOLOGY ROOM",
)


def _star_locations() -> pd.DataFrame:
    return pd.read_sql(
        """
    SELECT
        lo.location_id,
        lo.location_string,
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
    return pd.read_sql(
        """SELECT DepartmentKey,
            BedEpicId,
            Name,
            DepartmentName,
            RoomName,
            BedName,
            IsBed,
            BedInCensus,
            IsDepartment,
            IsRoom,
            IsCareArea,
            DepartmentExternalName,
            DepartmentSpecialty,
            DepartmentType,
            DepartmentServiceGrouper,
            DepartmentLevelOfCareGrouper,
            LocationName,
            ParentLocationName,
            _CreationInstant,
            _LastUpdatedInstant
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
        caboodle_departments_df["DepartmentName"].isin(DEPARTMENTS), :
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
            x["speciality"],
            x["department"],
            x["room"],
            x["hl7_bed"].lower(),
        ),
        axis=1,
    )

    # Still left with dups so now choose the most recent
    caboodle_departments_df.sort_values(
        by=["DepartmentName", "RoomName", "BedName", "_CreationInstant"], inplace=True
    )
    caboodle_departments_df.drop_duplicates(
        subset=["DepartmentName", "RoomName", "BedName"], keep="last", inplace=True
    )

    # Make key to merge and force to lower etc
    caboodle_departments_df["merge_key"] = caboodle_departments_df.agg(
        lambda x: (
            x["DepartmentSpecialty"],
            x["DepartmentName"],
            x["RoomName"],
            x["Name"].lower(),
        ),
        axis=1,
    )

    return star_locations_df.merge(
        caboodle_departments_df,
        how="left",
        on="merge_key",
        indicator=True,
        validate="one_to_one",
    ).drop("merge_key", axis="columns")


def _fetch_beds() -> list[list[str]]:
    star_locations_df = _star_locations()
    caboodle_departments_df = _caboodle_departments()
    beds_df = _merge_star_and_caboodle_beds(star_locations_df, caboodle_departments_df)

    rows = [beds_df.columns.tolist()]
    rows.extend(beds_df.values.tolist())
    return rows


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self):
        return self.message


def _create_admin_user(settings: BaserowSettings):
    logging.info("Creating admin user.")
    response = requests.post(
        f"{settings.public_url}/api/user/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "name": settings.username,
                "email": settings.email,
                "password": settings.password.get_secret_value(),
            }
        ),
    )

    if response.status_code == 400:
        logging.warning("response %d: %s.", response.status_code, response.content)
        if response.json()["error"] != "ERROR_EMAIL_ALREADY_EXISTS":
            raise BaserowException(f"response code {response.status_code}")

        logging.warning("User %s already created.", settings.username)
        return
    elif response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    logging.info("Admin user created.")


def _get_admin_user_auth_token(settings: BaserowSettings) -> str:
    response = requests.post(
        f"{settings.public_url}/api/user/token-auth/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "email": settings.email,
                "password": settings.password.get_secret_value(),
            }
        ),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    return cast(str, response.json()["token"])


def _get_group_id(settings: BaserowSettings, auth_token: str) -> int:
    logging.info("Getting default group_id.")
    response = requests.get(
        f"{settings.public_url}/api/groups/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    data = response.json()
    group = data[0]
    group_name = group["name"]
    group_id = group["id"]
    logging.info(f"Using group '{group_name} with id {group_id}.")
    return cast(int, group_id)


def _create_application(
    settings: BaserowSettings, auth_token: str, group_id: int
) -> int:

    logging.info("Checking to see if application hyui is already created.")
    response = requests.get(
        f"{settings.public_url}/api/applications/group/{group_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    application_id = next(
        (row["id"] for row in response.json() if row["name"] == "hyui"), None
    )
    if application_id:
        logging.warning("Application hyui already exists.")
        return cast(int, application_id)

    logging.info("Creating application hyui.")
    response = requests.post(
        f"{settings.public_url}/api/applications/group/{group_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
        data=json.dumps({"name": "hyui", "type": "database"}),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    return cast(int, response.json()["id"])


def _create_beds_table(
    settings: BaserowSettings,
    auth_token: str,
    application_id: int,
    beds: list[list[str]],
):
    logging.info("Checking to see if beds table already exists.")
    response = requests.get(
        f"{settings.public_url}/api/database/tables/database/{application_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    beds_table_id = next(
        (row["id"] for row in response.json() if row["name"] == "beds"), None
    )
    if beds_table_id:
        logging.warning(f"A table called beds already exists with id {beds_table_id}")
        return

    response = requests.post(
        f"{settings.public_url}/api/database/tables/database/{application_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
        data=json.dumps(
            {
                "name": "beds",
                "data": beds,
                "first_row_header": True,
            }
        ),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    logging.info("Table called beds created.")


def initialise_baserow():
    settings = get_baserow_settings()
    logging.info("Starting Baserow initialisation.")
    _create_admin_user(settings)
    auth_token = _get_admin_user_auth_token(settings)
    group_id = _get_group_id(settings, auth_token)
    application_id = _create_application(settings, auth_token, group_id)

    beds = _fetch_beds()
    _create_beds_table(settings, auth_token, application_id, beds)
