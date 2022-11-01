import requests


def get_rows(baserow_url: str, token: str, table_id: int, params: dict) -> list[dict]:
    """
    Baserow only returns 200 rows at the most. This function pages through an
    endpoint until all rows are returned.
    """
    rows_url = f"{baserow_url}/api/database/rows/table/{table_id}"
    headers = {"Authorization": f"Token {token}"}

    params["page"] = 0

    rows = []
    while True:

        params["page"] = params["page"] + 1
        response = requests.get(rows_url, headers=headers, params=params).json()
        rows.extend(response["results"])

        if not response["next"]:
            break

    return rows


def get_fields(baserow_url: str, token: str, table_id: int) -> dict[str, int]:
    url = f"{baserow_url}/api/database/fields/table/{table_id}/"
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(url, headers=headers)
    return {row["name"]: row["id"] for row in response.json()}
