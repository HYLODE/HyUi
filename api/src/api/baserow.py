import json
import requests
import warnings
from typing import Any, Tuple, cast

from api.config import Settings, get_settings
from api.utils import Timer


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


def _get_user_auth_token(
    baserow_url: str, email: str, password: str
) -> Tuple[str, str]:
    response = requests.post(
        f"{baserow_url}/api/user/token-auth/",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"email": email, "password": password}),
    )
    # access tokens valid for 10m
    # refresh tokens valid for 168h
    warnings.warn("Authenticating via username/password")

    if response.status_code == 200:
        access_token = cast(str, response.json()["access_token"])
        refresh_token = cast(str, response.json()["refresh_token"])
    else:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
        )

    # see https://api.baserow.io/api/redoc/#tag/User/operation/token_auth
    # Response sample
    # {
    #   "user": {
    #     "first_name": "string",
    #     "username": "user@example.com",
    #     "language": "string"
    #   },
    #   "token": "string",
    #   "access_token": "string",
    #   "refresh_token": "string"
    # }
    # Note that in the above access_token == token
    return access_token, refresh_token


def _refresh_user_auth_token(baserow_url: str) -> str:
    # access tokens valid for 10m
    # refresh tokens valid for 168h
    warnings.warn("Refreshing user authentication")
    refresh_token = BASEROW_REFRESH_TOKEN  # from the outer scope
    response = requests.post(
        f"{baserow_url}/api/user/token-refresh/",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"refresh_token": refresh_token}),
    )

    if response.status_code == 200:
        access_token = cast(str, response.json()["access_token"])
        global BASEROW_AUTH_TOKEN
        BASEROW_AUTH_TOKEN = access_token
    else:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
        )
    return access_token


def _auth_headers(auth_token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {auth_token}",
    }


def _get_application_id(
    baserow_url: str, auth_token: str, application_name: str
) -> int | None:
    def _request():
        return requests.get(
            f"{baserow_url}/api/applications/",
            headers=_auth_headers(auth_token),
        )

    response = _request()

    if response.status_code == 401:
        warnings.warn("Authentication error: will attempt to refresh")
        _refresh_user_auth_token(baserow_url)
        response = _request()

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
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

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
        )

    return next(
        (cast(int, row["id"]) for row in response.json() if row["name"] == table_name),
        None,
    )


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
    with Timer(text="get_rows.auth_token: Elapsed time: {:.4f}"):
        # auth_token = _get_user_auth_token(baserow_url, email, password)
        auth_token = BASEROW_AUTH_TOKEN

    with Timer(text="get_rows.application_id: Elapsed time: {:.4f}"):
        application_id = _get_application_id(baserow_url, auth_token, application_name)
    if not application_id:
        raise BaserowException(f"no application ID for application {application_name}")

    with Timer(text="get_rows.table_id: Elapsed time: {:.4f}"):
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
                rows_url, headers=_auth_headers(auth_token), params=params
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
    response = requests.get(url, headers=_auth_headers(auth_token))

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
        url, headers=_auth_headers(auth_token), params=params, json=payload
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
