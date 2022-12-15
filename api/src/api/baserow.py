from typing import cast

import requests


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self):
        return self.message


def _auth_headers(auth_token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {auth_token}",
    }


def _get_application_id(
    base_url: str, auth_token: str, application_name: str
) -> int | None:
    response = requests.get(
        f"{base_url}/api/applications/",
        headers=_auth_headers(auth_token),
    )

    return next(
        (
            cast(int, row["id"])
            for row in response.json()
            if row["name"] == application_name
        ),
        None,
    )


def _get_table_id(
    baserow_url: str, auth_token: str, application_id: int, table_name: str
) -> int | None:
    response = requests.get(
        f"{baserow_url}/api/database/tables/database/{application_id}/",
        headers=_auth_headers(auth_token),
    )

    return next(
        (cast(int, row["id"]) for row in response.json() if row["name"] == table_name),
        None,
    )


def get_rows(
    baserow_url: str,
    auth_token: str,
    application_name: str,
    table_name: str,
    params: dict,
) -> list[dict]:
    """
    Baserow only returns 200 rows at the most. This function pages through an
    endpoint until all rows are returned.
    """
    application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    table_id = _get_table_id(baserow_url, auth_token, application_id, table_name)
    if not table_id:
        raise BaserowException(
            f"no table ID for application {application_name}, table {table_name}"
        )

    rows_url = f"{baserow_url}/api/database/rows/table/{table_id}/"

    params["page"] = 0

    rows = []
    while True:

        params["page"] = params["page"] + 1
        response = requests.get(
            rows_url, headers=_auth_headers(auth_token), params=params
        ).json()
        rows.extend(response["results"])

        if not response["next"]:
            break

    return rows


def get_fields(
    baserow_url: str, auth_token: str, application_name: str, table_name: str
) -> dict[str, int]:
    application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    table_id = _get_table_id(baserow_url, auth_token, application_id, table_name)
    if not table_id:
        raise BaserowException(
            f"no table ID for application {application_name}, table {table_name}"
        )

    url = f"{baserow_url}/api/database/fields/table/{table_id}/"
    response = requests.get(url, headers=_auth_headers(auth_token))
    return {row["name"]: row["id"] for row in response.json()}
