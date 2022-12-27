import json
import logging
from pathlib import Path
from typing import cast

import pandas as pd
import requests
from models.beds import Bed

from initialise.config import BaserowSettings, get_baserow_settings
from initialise.convert import parse_to_data_frame
from initialise.db import caboodle_engine, star_engine
from . import DEPARTMENTS, VIRTUAL_BEDS, VIRTUAL_ROOMS


def _star_locations() -> pd.DataFrame:
    # noinspection SqlResolve
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
            x["speciality"],
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
            x["department_speciality"],
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


def _merge_default_properties(beds_df: pd.DataFrame) -> pd.DataFrame:
    """
    appends default properties to beds
    e.g. map positions, closed status etc.
    """
    with open(Path(__file__).parent / "bed_defaults.json", "r") as f:
        defaults = json.load(f)
    defaults_df = parse_to_data_frame(defaults, Bed)
    df = beds_df.merge(
        defaults_df, how="left", left_on="location_string", right_on="location_string"
    )
    return df


def _fetch_beds() -> list[list[str]]:
    star_locations_df = _star_locations()
    caboodle_departments_df = _caboodle_departments()
    beds_df = _merge_star_and_caboodle_beds(star_locations_df, caboodle_departments_df)
    beds_df = _merge_default_properties(beds_df)
    # JSON does not handle 'NaN' etc
    # https://stackoverflow.com/a/41213102/992999
    beds_df = beds_df.fillna("")

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
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
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
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return cast(str, response.json()["token"])


def _auth_headers(auth_token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {auth_token}",
    }


def _get_group_id(base_url: str, auth_token: str) -> int:
    logging.info("Getting default group_id.")
    response = requests.get(
        f"{base_url}/api/groups/",
        headers=_auth_headers(auth_token),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    data = response.json()
    group = data[0]
    group_name = group["name"]
    group_id = group["id"]
    logging.info(f"Using group '{group_name} with id {group_id}.")
    return cast(int, group_id)


def _delete_default_application(base_url: str, auth_token: str, group_id: int):
    response = requests.get(
        f"{base_url}/api/applications/group/{group_id}/",
        headers=_auth_headers(auth_token),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    application_id = next(
        (row["id"] for row in response.json() if row["name"] == "hyui's company"), None
    )

    if not application_id:
        return

    logging.info('Deleting the default application "hyui\'s company"')
    response = requests.delete(
        f"{base_url}/api/applications/{application_id}/",
        headers=_auth_headers(auth_token),
    )
    if response.status_code != 204:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )


def _create_application(base_url: str, auth_token: str, group_id: int) -> int:
    logging.info("Checking to see if application hyui is already created.")
    response = requests.get(
        f"{base_url}/api/applications/group/{group_id}/",
        headers=_auth_headers(auth_token),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    application_id = next(
        (row["id"] for row in response.json() if row["name"] == "hyui"), None
    )
    if application_id:
        logging.warning("Application hyui already exists.")
        return cast(int, application_id)

    logging.info("Creating application hyui.")
    response = requests.post(
        f"{base_url}/api/applications/group/{group_id}/",
        headers=_auth_headers(auth_token),
        data=json.dumps({"name": "hyui", "type": "database"}),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return cast(int, response.json()["id"])


def _create_table(
    base_url: str,
    auth_token: str,
    application_id: int,
    table_name: str,
    data: list[list[str]],
) -> int:
    logging.info(f"Checking to see if {table_name} table already exists.")
    response = requests.get(
        f"{base_url}/api/database/tables/database/{application_id}/",
        headers=_auth_headers(auth_token),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    table_id = next(
        (row["id"] for row in response.json() if row["name"] == table_name), None
    )
    if table_id:
        raise BaserowException(
            f"table called {table_name} already exists with id {table_id}"
        )

    response = requests.post(
        f"{base_url}/api/database/tables/database/{application_id}/",
        headers=_auth_headers(auth_token),
        data=json.dumps(
            {
                "name": table_name,
                "data": data,
                "first_row_header": True,
            }
        ),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    table_id = response.json()["id"]

    logging.info(f"Table called beds created with ID {table_id}.")
    return cast(int, table_id)


def _add_table_field(
    base_url: str,
    auth_token: str,
    table_id: int,
    column_name: str,
    column_type: str,
    column_details: dict = None,
):
    logging.info(f"Adding column {column_name} to table {table_id}.")
    column_details = column_details if column_details else {}

    payload = dict(
        name=column_name,
        type=column_type,
    )

    # select_options: list[tuple[int, str, str]],
    if column_details.get("select_options"):
        select_options_dicts = [
            {"id": option[0], "value": option[1], "color": option[2]}
            for option in column_details.get("select_options")
        ]
        payload["select_options"] = select_options_dicts

    response = requests.post(
        f"{base_url}/api/database/fields/table/{table_id}/",
        headers=_auth_headers(auth_token),
        data=json.dumps(payload),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )


def _add_beds_fields(base_url: str, auth_token: str, beds_table_id: int):
    # _add_table_field(base_url, auth_token, beds_table_id, "closed",
    # "boolean", [])
    # _add_table_field(base_url, auth_token, beds_table_id, "covid",
    # "boolean", [])
    _add_table_field(
        base_url,
        auth_token,
        beds_table_id,
        "bed_physical",
        "multiple_select",
        [
            (1, "sideroom", "red"),
            (2, "ventilator", "red"),
            (3, "monitored", "red"),
            (4, "ensuite", "red"),
            (5, "virtual", "red"),
        ],
    )
    _add_table_field(
        base_url,
        auth_token,
        beds_table_id,
        "bed_functional",
        "multiple_select",
        [
            (1, "periop", "red"),
            (2, "ficm", "red"),
            (3, "gwb", "red"),
            (4, "wms", "red"),
            (5, "t06", "red"),
            (6, "north", "red"),
            (7, "south", "red"),
            (8, "plex", "red"),
            (9, "nhnn", "red"),
            (10, "hdu", "red"),
            (11, "icu", "red"),
        ],
    )


def initialise_baserow():
    settings = get_baserow_settings()

    logging.info("Starting Baserow initialisation.")

    _create_admin_user(settings)
    auth_token = _get_admin_user_auth_token(settings)

    group_id = _get_group_id(settings.public_url, auth_token)

    _delete_default_application(settings.public_url, auth_token, group_id)

    application_id = _create_application(settings.public_url, auth_token, group_id)

    # Create the discharge_statuses table.
    discharge_statuses_table_id = _create_table(
        settings.public_url, auth_token, application_id, "discharge_statuses", [["csn"]]
    )
    _add_table_field(
        settings.public_url,
        auth_token,
        discharge_statuses_table_id,
        column_name="status",
        column_type="text",
    )

    _add_table_field(
        settings.public_url,
        auth_token,
        discharge_statuses_table_id,
        column_name="modified_at",
        column_type="date",
        column_details={
            "date_format": "ISO",
            "date_include_time": True,
            "date_time_format": "24",
        },
    )

    # Create the beds table.
    beds_rows = _fetch_beds()
    beds_table_id = _create_table(
        settings.public_url, auth_token, application_id, "beds", beds_rows
    )
    _add_beds_fields(settings.public_url, auth_token, beds_table_id)
