import argparse
import logging
import warnings
from pathlib import Path
from initialise.baserow import (
    BaserowException,
    _add_misc_fields,
    _add_table_row_batch,
    _create_admin_user,
    _create_application,
    _delete_default_application,
    _get_admin_user_auth_token,
    _get_group_id,
)
from initialise.beds import (
    _add_beds_user_fields,
    _create_bed_bones_table,
    _create_beds_user_table,
    _load_beds_user_defaults,
)
from initialise.beds_build import _fetch_beds
from initialise.config import get_baserow_settings
from initialise.departments import (
    _add_departments_fields,
    _create_departments_table,
    _load_department_defaults,
)
from initialise.rooms import _load_room_defaults, _create_rooms_table, _add_rooms_fields

from initialise.discharge_status import (
    _add_discharge_status_fields,
    _create_discharge_status_table,
)


def _set_log_level(level: str) -> None:
    log_level = logging.INFO
    match level:
        case "WARN":
            log_level = logging.WARNING
        case "DEBUG":
            log_level = logging.DEBUG

    logging.basicConfig(level=log_level)


def _start_operation(system: str) -> None:
    match system:
        case "baserow":
            initialise_baserow()
        case "recreate_defaults":
            recreate_defaults()


def initialise_baserow() -> None:
    """
    First run initialisation of Baserow
    - creates the beds table (from the caboodle/emap wrangling)
    - creates an empty discharge status table
    """
    settings = get_baserow_settings()

    logging.info("Starting Baserow initialisation.")
    _create_admin_user(settings)
    auth_token = _get_admin_user_auth_token(settings)
    group_id = _get_group_id(settings.public_url, auth_token)
    _delete_default_application(settings.public_url, auth_token, group_id)
    application_id = _create_application(settings.public_url, auth_token, group_id)
    logging.info(f"Baserow application with ID {application_id} created.")

    try:
        logging.info("Creating discharge_statuses table")
        discharge_statuses_table_id = _create_discharge_status_table(
            settings.public_url, auth_token, application_id
        )
        _add_discharge_status_fields(
            settings.public_url, auth_token, discharge_statuses_table_id
        )

    except BaserowException as e:
        print(e)
        warnings.warn("discharge_statuses table NOT created")

    try:
        logging.info("Creating beds table")
        bed_bones_table_id = _create_bed_bones_table(
            settings.public_url, auth_token, application_id
        )

        beds_df = _fetch_beds()

        cols_text = [
            "location_string",
            "hl7_department",
            "hl7_room",
            "hl7_bed",
            "department",
            "speciality",
            "room",
            "department_name",
            "department_external_name",
            "department_speciality",
            "department_type",
            "department_service_grouper",
            "department_level_of_care_grouper",
            "location_name",
            "parent_location_name",
        ]

        beds_df.fillna(
            {
                "bed_id": -1,
                "department_id": -1,
                "location_id": -1,
                "room_id": -1,
            },
            inplace=True,
        )

        cols_bool = [
            "is_room",
            "is_care_area",
        ]

        cols_int = [
            "location_id",
            "department_id",
            "room_id",
            "bed_id",
        ]

        # handle missingness in integers;
        # avoid decimal places if derived from floats
        for col in cols_int:
            beds_df[col].fillna(-1, inplace=True)
            beds_df[col] = beds_df[col].astype(int)

        _add_misc_fields(
            settings.public_url,
            auth_token,
            bed_bones_table_id,
            cols_int=cols_int,
            cols_bool=cols_bool,
            cols_text=cols_text,
        )
        # TODO:
        # 2. then use the batch update approach to load 200 rows at a time
        while beds_df.shape[0] > 0:
            _add_table_row_batch(
                settings.public_url, auth_token, bed_bones_table_id, beds_df[:200]
            )
            beds_df = beds_df[200:]

    except BaserowException as e:
        print(e)
        warnings.warn("beds bones table NOT created")


def recreate_defaults() -> None:
    """
    Update an existing instance of baserow adjustments to default tables
    - loads fresh versions of the default tables including
        - departments
    Returns:
    """
    settings = get_baserow_settings()

    # TODO: wrap this up in a single shell script for convenience
    logging.info(
        """
        Starting Baserow updates. WARNING this is destructive and
        will delete existing tables if replace==True
        ==================================================
        CHECK you have recreated the defaults as necessary
        e.g. run
        bed_make_defaults.py
        rooms_make_defaults.py
        departments_make_defaults.py

        only after this will baserow be properly updated
        """
    )

    auth_token = _get_admin_user_auth_token(settings)
    group_id = _get_group_id(settings.public_url, auth_token)
    application_id = _create_application(settings.public_url, auth_token, group_id)

    try:
        logging.info("Creating departments table")
        departments_table_id = _create_departments_table(
            settings.public_url, auth_token, application_id
        )
        _add_departments_fields(settings.public_url, auth_token, departments_table_id)
        df = _load_department_defaults(
            Path(__file__).parent / "json/department_defaults.json"
        )

        _add_table_row_batch(settings.public_url, auth_token, departments_table_id, df)

    except BaserowException as e:
        print(e)

    try:
        logging.info("Creating (user) rooms table")
        beds_table_id = _create_rooms_table(
            settings.public_url, auth_token, application_id
        )
        _add_rooms_fields(settings.public_url, auth_token, beds_table_id)
        df = _load_room_defaults(Path(__file__).parent / "json/room_defaults.json")
        # need to chunk this up as the batch load is limited to 200 rows
        while df.shape[0] > 0:
            _add_table_row_batch(
                settings.public_url, auth_token, beds_table_id, df[:200]
            )
            df = df[200:]

    except BaserowException as e:
        print(e)

    try:
        logging.info("Creating (user) beds table")
        beds_table_id = _create_beds_user_table(
            settings.public_url, auth_token, application_id
        )
        _add_beds_user_fields(settings.public_url, auth_token, beds_table_id)
        df = _load_beds_user_defaults(Path(__file__).parent / "json/bed_defaults.json")
        # need to chunk this up as the batch load is limited to 200 rows
        while df.shape[0] > 0:
            _add_table_row_batch(
                settings.public_url, auth_token, beds_table_id, df[:200]
            )
            df = df[200:]

    except BaserowException as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="HyUi Initialiser",
        description="Various functions to initialise the HyUi environment",
    )

    parser.add_argument(
        "--operation", choices=["baserow", "recreate_defaults"], required=True
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING"], default="INFO"
    )

    args = parser.parse_args()

    _set_log_level(args.log_level)
    _start_operation(args.operation)
