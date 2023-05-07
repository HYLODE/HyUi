import json
import time
import requests
from functools import lru_cache
from typing import Any, cast

from api.logger import logger, logger_timeit
from api.config import Settings, get_settings


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


def _request(url: str, auth_token: str) -> requests.Response:
    return requests.get(
        url=url,
        headers=_admin_auth_headers(auth_token),
    )


@logger_timeit()
def _get_user_auth_token(settings: Settings) -> dict[str, str]:
    """

    Uses username/password authentication to get a user access token that
    give admin privileges; permits a 1 minute pause if fails on first attempt;
    this is necessary when the API is started at the same time
    as the baserow application service

    Args:
        settings: read from the .env file; specifically needs a
            valid baserow username (email address) and password

    Returns:
        {access_token, refresh_token)
    """
    logger.info("Authenticating as admin via username/password")
    msg = """
    This typically happens on docker compose up.
    We need to wait for the base row container to be ready before asking for
    the user authentication token so we poll the baserow container a fixed
    number of times at fixed intervals and only fail if no token is available
    12 x 5 seconds (1 minute)
    """
    logger.debug(msg)

    @logger_timeit()
    def _request_token() -> Any:
        # access tokens valid for 10m
        # refresh tokens valid for 168h
        return requests.post(
            f"{settings.baserow_url}/api/user/token-auth/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "email": settings.baserow_email,
                    "password": settings.baserow_password.get_secret_value(),
                }
            ),
        )

    max_attempts, attempt = 12, 0
    while attempt < max_attempts:
        response = _request_token()
        if response.status_code == 502:
            logger.warning(
                f"Bad gateway on attempt {attempt}: check baserow "
                f"again in 5 seconds"
            )
            time.sleep(5)
            attempt += 1
            continue
        else:
            break

    # noinspection PyUnboundLocalVariable
    if response.status_code == 200:
        access_token = cast(str, response.json()["access_token"])
        refresh_token = cast(str, response.json()["refresh_token"])
    else:
        logger.error("Failed to authenticate as admin")
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
    logger.info("Refreshing user authentication")
    refresh_token = _get_user_auth_token(settings)["refresh_token"]
    response = requests.post(
        f"{settings.baserow_url}/api/user/token-refresh/",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"refresh_token": refresh_token}),
    )

    if response.status_code == 200:
        logger.success("Refreshed access token")
        access_token = cast(str, response.json()["access_token"])
    else:
        msg = (
            "ERROR: unable to refresh access token unexpected response {"
            "response.status_code}: {str(response.content)}"
        )
        logger.error(msg)
        raise BaserowException(msg)
    return access_token


@logger_timeit()
def _get_database_token(settings: Settings, auth_token: str, group_id: int) -> str:
    response = requests.get(
        url=f"{settings.baserow_url}/api/database/tokens/",
        headers=_admin_auth_headers(auth_token),
    )
    if response.status_code != 200:
        msg = f"Error {response.status_code}: unable to list database tokens"
        logger.error(msg)
        raise BaserowException(msg)
    token_list = [token for token in response.json() if token.get("group") == group_id]
    tokens = iter(token_list)

    try:
        token = next(tokens).get("key", "")
        logger.info("Using existing database read/write token")
        logger.info("Assumes that all tokens are equal with full permissions")
    except StopIteration:
        logger.info("Generating database read/write token")
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
            msg = f"Error {response.status_code}: unable to generate database token"
            logger.error(msg)
            raise BaserowException(msg)
    return token  # type: ignore


@logger_timeit()
def _get_group_id(settings: Settings, auth_token: str) -> int:
    logger.info("Getting default group_id.")
    response = requests.get(
        f"{settings.baserow_url}/api/groups/",
        headers=_admin_auth_headers(auth_token),
    )
    if response.status_code != 200:
        msg = f"unexpected response {response.status_code}: {str(response.content)}"
        logger.error(msg)
        raise BaserowException(msg)

    data = response.json()
    group = data[0]
    group_name = group["name"]
    group_id = group["id"]
    logger.info(f"Using group '{group_name} with id {group_id}.")
    return cast(int, group_id)


@logger_timeit()
def _get_application_id(settings: Settings, auth_token: str) -> int:
    def _request(auth_token: str) -> Any:
        return requests.get(
            f"{settings.baserow_url}/api/applications/",
            headers=_admin_auth_headers(auth_token),
        )

    response = _request(auth_token)

    if response.status_code == 401:
        logger.warning("Authentication error: will attempt to refresh")
        auth_token = _refresh_user_auth_token(settings)
        response = _request(auth_token)
        if response.status_code != 200:
            logger.error("Failed trying to refresh access token")
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


@logger_timeit()
def _get_table_dict(settings: Settings, auth_token: str, application_id: int) -> dict:
    """Return a dictionary of table ids, names, and a sub dict of fields and
    ids"""

    tables_url = (
        f"{settings.baserow_url}/api/database/tables/database" f"/{application_id}/"
    )
    response = _request(tables_url, auth_token)

    if response.status_code == 401:
        logger.warning("Authentication error: will attempt to refresh")
        auth_token = _refresh_user_auth_token(settings)
        response = _request(tables_url, auth_token)
        if response.status_code != 200:
            logger.error("Failed trying to refresh access token")
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    # table ids
    table_dict = {}
    for d in response.json():
        tid, name = d.get("id"), d.get("name")
        fields_url = f"{settings.baserow_url}/api/database/fields/table/{tid}/"
        response = _request(fields_url, auth_token)

        if response.status_code != 200:
            logger.error(f"Failed to fetch fields for table {name}")
            raise BaserowException(f"{str(response.content)}")

        fields = {row["name"]: row["id"] for row in response.json()}

        table_dict[name] = dict(
            id=tid,
            name=name,
            fields=fields,
        )

    return table_dict


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


class BaserowDB:
    # Redefine all the function names here else not availalbe at class scope
    # for the instance of the class
    _admin_auth_headers = _admin_auth_headers
    _simple_auth_headers = _simple_auth_headers

    def __init__(
        self,
        settings: Settings,
        database_token: str,
        tables_dict: dict,
    ) -> None:
        self.baserow_url = settings.baserow_url
        self.database_token = database_token
        self.tables_dict = tables_dict

    @logger_timeit()
    def get_fields(self, table_name: str) -> dict[str, int]:
        auth_token = self.database_token
        table_id = self.tables_dict.get(table_name, {}).get("id")

        url = f"{self.baserow_url}/api/database/fields/table/{table_id}/"
        response = requests.get(url, headers=_simple_auth_headers(auth_token))

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

        return {row["name"]: row["id"] for row in response.json()}

    @logger_timeit()
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
        table_id = self.tables_dict.get(table_name, {}).get("id")
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

    @logger_timeit()
    def post_row(
        self,
        table_name: str,
        params: dict,
        payload: dict,
    ) -> Any:
        auth_token = self.database_token
        table_id = self.tables_dict.get(table_name, {}).get("id")
        url = f"{self.baserow_url}/api/database/rows/table/{table_id}/"

        response = requests.post(
            url, headers=_simple_auth_headers(auth_token), params=params, json=payload
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
    logger.info("Baserow module initiation")
    settings = get_settings()

    logger.info("Generating admin token")
    admin_token = _get_user_auth_token(settings)["access_token"]

    logger.info("Getting database token")
    group_id = _get_group_id(settings, admin_token)
    database_token = _get_database_token(settings, admin_token, group_id)

    logger.info("Getting application ID")
    application_id = _get_application_id(settings, admin_token)

    logger.info("Getting tables dictionary")
    tables_dict = _get_table_dict(settings, admin_token, application_id)

    return BaserowDB(
        settings=settings,
        database_token=database_token,
        tables_dict=tables_dict,
    )
