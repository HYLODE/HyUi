import json
import logging
import requests
import warnings
from functools import lru_cache
from typing import Any, cast

from api.config import Settings, get_settings
from api.utils import Timer


def _admin_auth_headers(token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {token}",
    }


def _simple_auth_headers(token: str) -> dict[str, str]:
    """
    User not admin authentication
    > Baserow uses a simple token based authentication. You need to generate
    at least one database token in your settings to use the endpoints
    described below.
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
    }


@Timer(text="Getting admin auth token: Elapsed time {:0.4f} seconds")
def _get_user_auth_token(settings: Settings) -> dict[str, str]:
    response = requests.post(
        f"{settings.baserow_url}/api/user/token-auth/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "email": settings.baserow_email,
                "password": settings.baserow_password.get_secret_value(),
            }
        ),
    )
    # access tokens valid for 10m
    # refresh tokens valid for 168h
    logging.warning("Authenticating as admin via username/password")

    if response.status_code == 200:
        access_token = cast(str, response.json()["access_token"])
        refresh_token = cast(str, response.json()["refresh_token"])
    else:
        logging.error("Failed to authenticate as admin")
        import pdb

        pdb.set_trace()
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    baserow_tokens = {"access_token": access_token, "refresh_token": refresh_token}
    return baserow_tokens


def _refresh_user_auth_token(settings: Settings) -> str:
    # access tokens valid for 10m
    # refresh tokens valid for 168h
    warnings.warn("Refreshing user authentication")
    refresh_token = _get_user_auth_token(settings)["refresh_token"]
    response = requests.post(
        f"{settings.baserow_url}/api/user/token-refresh/",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"refresh_token": refresh_token}),
    )

    if response.status_code == 200:
        print("SUCCESS: refreshed access token")
        access_token = cast(str, response.json()["access_token"])
    else:
        raise BaserowException(
            "ERROR: unable to refresh access token"
            f"unexpected response {response.status_code}: "
            f"{str(response.content)}"
        )
    return access_token


def _get_group_id(settings: Settings, auth_token: str) -> int:
    logging.info("Getting default group_id.")
    response = requests.get(
        f"{settings.baserow_url}/api/groups/",
        headers=_admin_auth_headers(auth_token),
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


def _get_application_id(settings: Settings, auth_token: str) -> int:
    def _request(auth_token: str) -> Any:
        return requests.get(
            f"{settings.baserow_url}/api/applications/",
            headers=_admin_auth_headers(auth_token),
        )

    response = _request(auth_token)

    if response.status_code == 401:
        warnings.warn("Authentication error: will attempt to refresh")
        auth_token = _refresh_user_auth_token(settings)
        response = _request(auth_token)
        if response.status_code != 200:
            warnings.warn("ERROR Failed trying to refresh access token")
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: "
            f""
            f"{str(response.content)}"
        )

    return next(
        (
            cast(int, row["id"])
            for row in response.json()
            if row["name"] == settings.baserow_application_name
        )
    )


def _get_table_ids(settings: Settings, auth_token: str, application_id: int) -> dict:
    """Return a dictionary of table names and ids"""

    url = (
        f"{settings.baserow_url}/api/database/tables/database/" f"" f"{application_id}/"
    )

    def _request(url: str, auth_token: str) -> requests.Response:
        return requests.get(
            url=url,
            headers=_admin_auth_headers(auth_token),
        )

    response = _request(url, auth_token)

    if response.status_code == 401:
        warnings.warn("Authentication error: will attempt to refresh")
        auth_token = _refresh_user_auth_token(settings)
        response = _request(url, auth_token)
        if response.status_code != 200:
            warnings.warn("ERROR Failed trying to refresh access token")
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}"
            f": "
            f"{str(response.content)}"
        )

    lofd = response.json()  # lofd=list of dict
    return {d.get("name"): d.get("id") for d in lofd}  #


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


class BaserowDB:
    @staticmethod
    def _get_database_token(settings: Settings, auth_token: str, group_id: int) -> str:

        response = requests.get(
            url=f"{settings.baserow_url}/api/database/tokens/",
            headers=_admin_auth_headers(auth_token),
        )
        if response.status_code != 200:
            raise BaserowException(
                f"Error {response.status_code}: unable to " f"list database " f"tokens"
            )
        token_list = [
            token for token in response.json() if token.get("group") == group_id
        ]
        tokens = iter(token_list)

        try:
            token = next(tokens).get("key", "")
            logging.info("Using existing database read/write token")
            warnings.warn("Assumes that all tokens are equal with full " "permissions ")
        except StopIteration:
            logging.info("Generating database read/write token")
            response = requests.post(
                url=f"{settings.baserow_url}/api/database/tokens/",
                headers=_admin_auth_headers(auth_token),
                json=dict(
                    name=settings.baserow_username,
                    group=group_id,
                ),
            )

            if response.status_code == 200:
                token = response.json().get("key", "")
            else:
                raise BaserowException(
                    f"Error {response.status_code}: unable to "
                    f"generate database token"
                )
        return token  # type: ignore

    logging.warning("Initiating class methods for BaserowDB")
    settings = get_settings()
    logging.warning("Generating admin token")
    admin_token = _get_user_auth_token(settings)["access_token"]
    logging.warning("Getting database token")
    group_id = _get_group_id(settings, admin_token)
    database_token = _get_database_token(
        settings,
        admin_token,
        group_id,
    )
    application_id = _get_application_id(
        settings,
        admin_token,
    )
    tables_dict = _get_table_ids(settings, admin_token, application_id)
    logging.info(str(tables_dict))

    # Redefine all the function names here else not availalbe at class scope
    # for the instance of the class
    _admin_auth_headers = _admin_auth_headers
    _simple_auth_headers = _simple_auth_headers
    _get_user_auth_token = _get_user_auth_token
    _refresh_user_auth_token = _refresh_user_auth_token

    def __init__(self) -> None:

        self.baserow_url = BaserowDB.settings.baserow_url
        self.database_token = BaserowDB.database_token
        self.tables_dict = BaserowDB.tables_dict

    def get_rows(
        self,
        table_name: str,
        params: dict,
    ) -> list[dict]:
        """
        Baserow only returns 200 rows at the most. This function pages
        through an
        endpoint until all rows are returned.
        """
        # auth_token = self._get_user_auth_token()["access_token"]
        auth_token = self.database_token
        table_id = self.tables_dict.get(table_name)
        rows_url = f"{self.baserow_url}/api/database/rows/table/{table_id}/"

        params["page"] = 0

        rows = []
        while True:

            params["page"] = params["page"] + 1
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

    def get_fields(self, table_name: str) -> dict[str, int]:

        auth_token = self.database_token
        table_id = self.tables_dict.get(table_name)

        url = f"{self.baserow_url}/api/database/fields/table/{table_id}/"
        response = requests.get(url, headers=_simple_auth_headers(auth_token))

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

        return {row["name"]: row["id"] for row in response.json()}

    def post_row(
        self,
        table_name: str,
        params: dict,
        payload: dict,
    ) -> Any:

        auth_token = self.database_token
        table_id = self.tables_dict.get(table_name)
        url = f"{self.baserow_url}/api/database/rows/table/{table_id}/"

        response = requests.post(
            url, headers=_admin_auth_headers(auth_token), params=params, json=payload
        )

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f""
                f"{str(response.content)}"
            )

        return response.json()


@lru_cache()
def get_baserow_db() -> BaserowDB:
    return BaserowDB()
