import argparse
import logging
import warnings

from .baserow import (
    BaserowException,
    _add_table_row,
    _add_table_row_batch,
    _create_admin_user,
    _create_application,
    _delete_default_application,
    _get_admin_user_auth_token,
    _get_group_id,
)
from .beds import _add_beds_fields, _create_beds_table
from .beds_build import _fetch_beds
from .config import get_baserow_settings
from .departments import (
    _add_departments_fields,
    _create_departments_table,
    _load_department_defaults,
)
from .discharge_status import (
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
        beds_table_id = _create_beds_table(
            settings.public_url, auth_token, application_id
        )

        _add_beds_fields(settings.public_url, auth_token, beds_table_id)

        beds_df = _fetch_beds()

        for row in beds_df.itertuples():
            _add_table_row(
                settings.public_url,
                auth_token,
                beds_table_id,
                {"location": row["location"]},
            )
    except BaserowException as e:
        print(e)
        warnings.warn("beds table NOT created")


def recreate_defaults() -> None:
    """
    Update an existing instance of baserow adjustments to default tables
    - loads fresh versions of the default tables including
        - departments
    Returns:
    """
    settings = get_baserow_settings()

    logging.info(
        "Starting Baserow updates. WARNING this is destructive and "
        "will delete the existing department table"
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
        df = _load_department_defaults()

        _add_table_row_batch(settings.public_url, auth_token, departments_table_id, df)

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
