import requests

from api.config import BaserowSettings, Settings
from api.utils import Timer


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


def _simple_auth_headers(simple_auth_token: str) -> dict[str, str]:
    """
    User not admin authentication
    > Baserow uses a simple token based authentication. You need to generate
    at least one database token in your settings to use the endpoints
    described below.
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {simple_auth_token}",
    }


def _get_table_id(
    settings_baserow: BaserowSettings,
    table_name: str,
) -> int | None:
    table_id = settings_baserow.dict().get(f"table_{table_name}", None)
    if not table_id:
        raise BaserowException(f"Table {table_name} not found in .env.baserow?")
    return table_id


def get_rows(
    settings_baserow: BaserowSettings,
    settings: Settings,
    table_name: str,
    params: dict,
) -> list[dict]:
    """
    Baserow only returns 200 rows at the most. This function pages through an
    endpoint until all rows are returned.
    """
    auth_token = settings_baserow.read_write_token.get_secret_value()
    table_id = _get_table_id(settings_baserow, table_name)
    baserow_url = settings.baserow_url

    rows_url = f"{baserow_url}/api/database/rows/table/{table_id}/"

    params["page"] = 0

    rows = []
    while True:

        params["page"] = params["page"] + 1
        with Timer(text="get_rows.requests: Elapsed time: {:.4f}"):
            response = requests.get(
                rows_url, headers=_simple_auth_headers(auth_token), params=params
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
    settings_baserow: BaserowSettings, settings: Settings, table_name: str
) -> dict[str, int]:
    # auth_token = _get_user_auth_token(baserow_url, email, password)

    auth_token = settings_baserow.read_write_token.get_secret_value()
    baserow_url = settings.baserow_url
    table_id = _get_table_id(settings_baserow, table_name)
    url = f"{baserow_url}/api/database/fields/table/{table_id}/"

    response = requests.get(url, headers=_simple_auth_headers(auth_token))

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return {row["name"]: row["id"] for row in response.json()}


def post_row(
    settings_baserow: BaserowSettings,
    settings: Settings,
    table_name: str,
    params: dict,
    payload: dict,
) -> dict:
    auth_token = settings_baserow.read_write_token.get_secret_value()
    baserow_url = settings.baserow_url
    table_id = _get_table_id(settings_baserow, table_name)

    url = f"{baserow_url}/api/database/rows/table/{table_id}/"

    response = requests.post(
        url, headers=_simple_auth_headers(auth_token), params=params, json=payload
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: " f"{str(response.content)}"
        )

    return response.json()  # type: ignore
