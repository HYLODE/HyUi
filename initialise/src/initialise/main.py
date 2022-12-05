import json
import logging
from typing import cast

import requests

from initialise.config import get_baserow_settings, BaserowSettings


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
            f"unexpected response {response.status_code}: {str(response.content)}"
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
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    return cast(str, response.json()["token"])


def _get_group_id(settings: BaserowSettings, auth_token: str) -> int:
    logging.info("Getting default group_id.")
    response = requests.get(
        f"{settings.public_url}/api/groups/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    data = response.json()
    group = data[0]
    group_name = group["name"]
    group_id = group["id"]
    logging.info(f"Using group '{group_name} with id {group_id}.")
    return cast(int, group_id)


def _create_application(
    settings: BaserowSettings, auth_token: str, group_id: int
) -> int:

    logging.info("Checking to see if application hyui is already created.")
    response = requests.get(
        f"{settings.public_url}/api/applications/group/{group_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    application_id = next(
        (row["id"] for row in response.json() if row["name"] == "hyui"), None
    )
    if application_id:
        logging.warning("Application hyui already exists.")
        return cast(int, application_id)

    logging.info("Creating application hyui.")
    response = requests.post(
        f"{settings.public_url}/api/applications/group/{group_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
        data=json.dumps({"name": "hyui", "type": "database"}),
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    return cast(int, response.json()["id"])


def _create_beds_table(settings: BaserowSettings, auth_token: str, application_id: int):
    logging.info("Checking to see if beds table already exists.")
    response = requests.get(
        f"{settings.public_url}/api/database/tables/database/{application_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
    )
    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    beds_table_id = next(
        (row["id"] for row in response.json() if row["name"] == "beds"), None
    )
    if beds_table_id:
        logging.warning(f"A table called beds already exists with id {beds_table_id}")
        return

    response = requests.post(
        f"{settings.public_url}/api/database/tables/database/{application_id}/",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        },
        data=json.dumps(
            {
                "name": "beds",
                "data": [
                    ["bed_code", "ward"],
                    ["BC", "W"],
                ],
                "first_row_header": True,
            }
        ),
    )

    if response.status_code != 200:
        raise BaserowException(
            f"unexpected response {response.status_code}: {str(response.content)}"
        )

    logging.info("Table called beds created.")


def initialise_baserow(settings: BaserowSettings):
    logging.info("Starting Baserow initialisation.")
    _create_admin_user(settings)
    auth_token = _get_admin_user_auth_token(settings)
    group_id = _get_group_id(settings, auth_token)
    application_id = _create_application(settings, auth_token, group_id)
    _create_beds_table(settings, auth_token, application_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialise_baserow(get_baserow_settings())
