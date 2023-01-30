import json
import requests
import warnings
from typing import Any, cast

from api.utils import Timer


class BaserowException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return self.message


class BaserowAuthenticator:
    def __init__(self, baserow_url: str, email: str, password: str):
        self.baserow_url = baserow_url
        self.email = email
        self.password = password

    def _get_user_auth_token(
        self,
    ) -> dict[str, str]:
        response = requests.post(
            f"{self.baserow_url}/api/user/token-auth/",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"email": self.email, "password": self.password}),
        )
        # access tokens valid for 10m
        # refresh tokens valid for 168h
        warnings.warn("Authenticating via username/password")

        if response.status_code == 200:
            access_token = cast(str, response.json()["access_token"])
            refresh_token = cast(str, response.json()["refresh_token"])
        else:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

        baserow_tokens = {"access_token": access_token, "refresh_token": refresh_token}
        return baserow_tokens

    def _refresh_user_auth_token(self) -> str:
        # access tokens valid for 10m
        # refresh tokens valid for 168h
        warnings.warn("Refreshing user authentication")
        # refresh_token = BASEROW_REFRESH_TOKEN  # from the outer scope
        refresh_token = self._get_user_auth_token()["refresh_token"]
        response = requests.post(
            f"{self.baserow_url}/api/user/token-refresh/",
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

    @staticmethod
    def _auth_headers(auth_token: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"JWT {auth_token}",
        }

    def _get_application_id(self, auth_token: str, application_name: str) -> int | None:
        def _request(auth_token: str) -> Any:
            return requests.get(
                f"{self.baserow_url}/api/applications/",
                headers=self._auth_headers(auth_token),
            )

        response = _request(auth_token)

        if response.status_code == 401:
            warnings.warn("Authentication error: will attempt to refresh")
            auth_token = self._refresh_user_auth_token()
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
                f"{str(response.content)}"
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
        self, auth_token: str, application_id: int, table_name: str
    ) -> int | None:
        def _request(auth_token: str) -> Any:
            return requests.get(
                f"{self.baserow_url}/api/database/tables/database/{application_id}/",
                headers=self._auth_headers(auth_token),
            )

        response = _request(auth_token)

        if response.status_code == 401:
            warnings.warn("Authentication error: will attempt to refresh")
            auth_token = self._refresh_user_auth_token()
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
                f"{str(response.content)}"
            )

        return next(
            (
                cast(int, row["id"])
                for row in response.json()
                if row["name"] == table_name
            ),
            None,
        )

    def get_rows(
        self,
        application_name: str,
        table_name: str,
        params: dict,
    ) -> list[dict]:
        """
        Baserow only returns 200 rows at the most. This function pages through an
        endpoint until all rows are returned.
        """
        auth_token = self._get_user_auth_token()["access_token"]
        application_id = self._get_application_id(auth_token, application_name)
        if not application_id:
            raise BaserowException(
                f"no application ID for application {application_name}"
            )

        table_id = self._get_table_id(auth_token, application_id, table_name)
        if not table_id:
            raise BaserowException(
                f"no table ID for application {application_name}, table "
                f"{table_name}"
            )

        rows_url = f"{self.baserow_url}/api/database/rows/table/{table_id}/"

        params["page"] = 0

        rows = []
        while True:

            params["page"] = params["page"] + 1
            with Timer(text="get_rows.requests: Elapsed time: {:.4f}"):
                response = requests.get(
                    rows_url, headers=self._auth_headers(auth_token), params=params
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

    def get_fields(self, application_name: str, table_name: str) -> dict[str, int]:
        auth_token = self._get_user_auth_token()["access_token"]

        application_id = self._get_application_id(auth_token, application_name)
        if not application_id:
            raise BaserowException(
                f"no application ID for application {application_name}"
            )

        table_id = self._get_table_id(auth_token, application_id, table_name)
        if not table_id:
            raise BaserowException(
                f"no table ID for application {application_name}, table "
                f"{table_name}"
            )

        url = f"{self.baserow_url}/api/database/fields/table/{table_id}/"
        response = requests.get(url, headers=self._auth_headers(auth_token))

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f"{str(response.content)}"
            )

        return {row["name"]: row["id"] for row in response.json()}

    def post_row(
        self,
        application_name: str,
        table_name: str,
        params: dict,
        payload: dict,
    ) -> Any:
        auth_token = self._get_user_auth_token()["access_token"]

        application_id = self._get_application_id(auth_token, application_name)
        if not application_id:
            raise BaserowException(
                f"no application ID for application {application_name}"
            )

        table_id = self._get_table_id(auth_token, application_id, table_name)
        if not table_id:
            raise BaserowException(
                f"no table ID for application {application_name}, table "
                f"{table_name}"
            )

        url = f"{self.baserow_url}/api/database/rows/table/{table_id}/"

        response = requests.post(
            url, headers=self._auth_headers(auth_token), params=params, json=payload
        )

        if response.status_code != 200:
            raise BaserowException(
                f"unexpected response {response.status_code}: "
                f""
                f"{str(response.content)}"
            )

        return response.json()
