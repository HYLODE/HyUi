import json

import requests

from initialise.config import get_settings


def initialise_baserow():
    settings = get_settings()
    base_url = settings.baserow_base_url

    response = requests.post(
        f"{base_url}/api/user/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "name": settings.baserow_username,
                "email": settings.baserow_email,
                "password": settings.baserow_password.get_secret_value(),
            }
        ),
    )

    if response.status_code == 400:
        if response.json()["error"] != "ERROR_EMAIL_ALREADY_EXISTS":
            raise Exception(f"response code {response.status_code}")
    elif response.status_code != 200:
        raise Exception(f"response code {response.status_code}: {response.json()}")

    response = requests.post(
        f"{base_url}/api/user/token-auth/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "email": settings.baserow_email,
                "password": settings.baserow_password.get_secret_value(),
            }
        ),
    )
    assert response.status_code == 200

    token = response.json()["token"]

    print(token)

    response = requests.get(
        f"{base_url}/api/groups/",
        headers={"Content-Type": "application/json", "Authorization": f"JWT {token}"},
    )
    assert response.status_code == 200

    group_id = response.json()[0]["id"]

    response = requests.post(
        f"{base_url}/api/applications/group/{group_id}/",
        headers={"Content-Type": "application/json", "Authorization": f"JWT {token}"},
        data=json.dumps({"name": "hyui", "type": "database"}),
    )
    assert response.status_code == 200

    application_id = response.json()["id"]

    response = requests.post(
        f"{base_url}/api/database/tables/database/{application_id}/",
        headers={"Content-Type": "application/json", "Authorization": f"JWT {token}"},
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

    assert response.status_code == 200


if __name__ == "__main__":
    initialise_baserow()
