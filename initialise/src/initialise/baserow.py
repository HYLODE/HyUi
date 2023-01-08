"""
Functions for managing the Baserow API
"""
# TODO: refactor: repeated code and complex long functions

import json
import logging
from typing import Any, cast

import pandas as pd
import requests

from .config import BaserowSettings


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


def _create_admin_user(settings: BaserowSettings) -> None:
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


def _delete_default_application(base_url: str, auth_token: str, group_id: int) -> None:
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
    primary_field_name: str,
    primary_field_data: dict[str, Any],
    replace: bool = False,
) -> int:
    """Creates a baserow table and returns the table ID. Baserow requires that
    the table has at least one column but does not allow you to specify what
    type that column should be on creation. Therefore, this function makes
    another API call after the table is created to update the primary field
    to the required type as described in `primary_field_data`.

    :param base_url: The Baserow base URL without a trailing slash.
    :param auth_token: Auth token to access Baserow API.
    :param application_id: Application ID to create the table in.
    :param table_name: The table name.
    :param primary_field_name: The name of the primary field. This cannot be id
        or order.
    :param primary_field_data: The dictionary to pass in when updating the
        primary field. Information of what can be used in this dictionary is
        found in the Baserow documentation in the `update_database_table_field`
        API documentation.
    :param replace: replace any pre-existing table with the same name

    :return: The newly created database table ID.
    """
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
        if replace:
            response = requests.delete(
                f"{base_url}/api/database/tables/{table_id}/",
                headers=_auth_headers(auth_token),
            )
            if response.status_code != 204:
                raise BaserowException(f"Failed to delete {table_name}")
        else:
            raise BaserowException(
                f"table called {table_name} already exists with id {table_id}"
            )

    response = requests.post(
        f"{base_url}/api/database/tables/database/{application_id}/",
        headers=_auth_headers(auth_token),
        data=json.dumps(
            {
                "name": table_name,
                "data": [[primary_field_name]],
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

    # Update the primary field to be the required type.
    if not primary_field_data:
        return cast(int, table_id)

    response = requests.get(
        f"{base_url}/api/database/fields/table/{table_id}/",
        headers=_auth_headers(auth_token),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    primary_field_id = next(
        (row["id"] for row in response.json() if row["name"] == primary_field_name),
        None,
    )

    if not primary_field_id:
        raise BaserowException("expected dummy_field_id")

    response = requests.patch(
        f"{base_url}/api/database/fields/{primary_field_id}/",
        headers=_auth_headers(auth_token),
        data=json.dumps(primary_field_data),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return cast(int, table_id)


def _add_table_field(
    base_url: str,
    auth_token: str,
    table_id: int,
    column_name: str,
    column_type: str,
    column_details: dict | None,
) -> None:
    logging.info(f"Adding column {column_name} to table {table_id}.")
    details = {}
    if column_details:
        details = column_details

    payload = dict(
        name=column_name,
        type=column_type,
    )  # type: dict[str, Any]
    payload.update(details)

    select_options = details.get("select_options")  # type: ignore
    if select_options:
        select_options_dicts = [
            {"id": option[0], "value": option[1], "color": option[2]}
            for option in select_options
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


def _add_table_row(
    base_url: str, auth_token: str, table_id: int, row: dict[str, Any]
) -> None:
    logging.info(f"Adding row table {table_id}.")

    response = requests.post(
        f"{base_url}/api/database/rows/table/{table_id}/?user_field_names=true",
        headers=_auth_headers(auth_token),
        data=json.dumps(row),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )


def _add_table_row_batch(
    base_url: str, auth_token: str, table_id: int, df: pd.DataFrame
) -> None:
    rows = df.to_dict(orient="records")
    logging.info(f"Adding {len(rows)} rows to table {table_id}.")

    response = requests.post(
        f"{base_url}/api/database/rows/table/"
        f"{table_id}/batch/?user_field_names=true",
        headers=_auth_headers(auth_token),
        json=dict(items=rows),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )


def _add_misc_fields(
    base_url: str,
    auth_token: str,
    table_id: int,
    cols_int: list[str],
    cols_bool: list[str],
    cols_text: list[str],
) -> None:
    """given lists of field names then creates fields"""
    # TODO: a better version would take a data frame and work this out for
    #  itself based on the existing dtypes

    cols_text = [
        "department",
        "room",
        "hl7_bed",
        "hl7_room",
        "hl7_department",
    ]
    for col in cols_text:
        _add_table_field(
            base_url,
            auth_token,
            table_id,
            column_name=col,
            column_type="text",
            column_details=None,
        )

    for col in cols_int:
        _add_table_field(
            base_url,
            auth_token,
            table_id,
            column_name=col,
            column_type="number",
            column_details={"number_negative": True},
        )

    for col in cols_bool:
        _add_table_field(base_url, auth_token, table_id, col, "boolean", {})
