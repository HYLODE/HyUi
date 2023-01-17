import requests
import warnings
from typing import Any, Tuple, cast
from fastapi import Depends

from api.config import Settings, get_settings
from api.utils import Timer

# TODO: use database not user tokens for read/write actions
# will need to be regenerated each time the application runs
# https://api.baserow.io/api/redoc/#tag/Database-tokens/operation/create_database_token

settings = get_settings()


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


def _simple_auth_headers(simple_auth_token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {simple_auth_token}",
    }


def _get_application_id(settings: Settings = Depends(get_settings)) -> int:
    return settings.baserow_application_id


def _get_table_id(
    settings: Settings,
    table_name: str,
) -> int | None:
    table_id = settings.dict().get(f"baserow_table_{table_name}")
    return table_id


_get_table_id(settings, "beds")


def get_rows(
    baserow_url: str,
    email: str,
    password: str,
    application_name: str,
    table_name: str,
    params: dict,
) -> list[dict]:
    """
    Baserow only returns 200 rows at the most. This function pages through an
    endpoint until all rows are returned.
    """
    auth_token = BASEROW_AUTH_TOKEN

    application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    table_id = _get_table_id(baserow_url, auth_token, application_id, table_name)
    if not table_id:
        raise BaserowException(
            f"no table ID for application {application_name}, table " f"{table_name}"
        )

    rows_url = f"{baserow_url}/api/database/rows/table/{table_id}/"

    params["page"] = 0

    rows = []
    while True:

        params["page"] = params["page"] + 1
        with Timer(text="get_rows.requests: Elapsed time: {:.4f}"):
            response = requests.get(
                rows_url, headers=_jwt_auth_headers(auth_token), params=params
            )

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

        data = response.json()
        rows.extend(data["results"])

        if not data["next"]:
            break

    return rows


def get_fields(
    baserow_url: str, email: str, password: str, application_name: str, table_name: str
) -> dict[str, int]:
    # auth_token = _get_user_auth_token(baserow_url, email, password)
    auth_token = BASEROW_AUTH_TOKEN

    application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    table_id = _get_table_id(baserow_url, auth_token, application_id, table_name)
    if not table_id:
        raise BaserowException(
            f"no table ID for application {application_name}, table " f"{table_name}"
        )

    url = f"{baserow_url}/api/database/fields/table/{table_id}/"
    response = requests.get(url, headers=_jwt_auth_headers(auth_token))

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
        )

    return {row["name"]: row["id"] for row in response.json()}


def post_row(
    baserow_url: str,
    email: str,
    password: str,
    application_name: str,
    table_name: str,
    params: dict,
    payload: dict,
) -> Any:
    # auth_token = _get_user_auth_token(baserow_url, email, password)
    auth_token = BASEROW_AUTH_TOKEN

    application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    table_id = _get_table_id(baserow_url, auth_token, application_id, table_name)
    if not table_id:
        raise BaserowException(
            f"no table ID for application {application_name}, table " f"{table_name}"
        )

    url = f"{baserow_url}/api/database/rows/table/{table_id}/"

    response = requests.post(
        url, headers=_jwt_auth_headers(auth_token), params=params, json=payload
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return response.json()


def _load_user_auth_token(settings: Settings) -> Tuple[str, str]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()
    return _get_user_auth_token(baserow_url, email, password)


settings = get_settings()
BASEROW_AUTH_TOKEN, BASEROW_REFRESH_TOKEN = _load_user_auth_token(settings)
