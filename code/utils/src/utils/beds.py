# src/utils/beds.py
"""
Methods for managing interaction with base row and beds bones
"""
from typing import List, Optional

import pandas as pd
import requests
from sqlmodel import SQLModel

from config.settings import settings


class BedBonesBase(SQLModel):

    id: int
    location_id: Optional[int]
    location_string: Optional[str]
    order: float
    department: str
    room: str
    bed: str
    unit_order: Optional[str]
    closed: Optional[bool]
    covid: Optional[bool]
    bed_functional: Optional[str]
    bed_physical: Optional[str]
    DischargeReady: Optional[str]


BED_BONES_TABLE_ID = 261
DEPARTMENT_FIELD_ID = 2041
CLOSED_BED_FIELD_ID = 2075

CORE_FIELDS = [
    "department",
    "room",
    "bed",
    "unit_order",
    "closed",
    "covid",
    "bed_functional",
    "bed_physical",
    "DischargeReady",
    "location_id",
    "location_string",
]


def get_closed_beds(
    table_id=BED_BONES_TABLE_ID,
    closed_bed_field_id=CLOSED_BED_FIELD_ID,
    fields=CORE_FIELDS,
    api_token=settings.BASEROW_READWRITE_TOKEN,
) -> list:
    """
    Queries the baserow API for a list of CLOSED beds

    :returns:   closed beds
    """

    url = f"{settings.BASEROW_URL}/api/database/rows/table/{table_id}/"

    if settings.VERBOSE:
        print(url)

    payload = {
        "user_field_names": "true",
        f"filter__field_{closed_bed_field_id}__boolean": True,
        "include": ",".join(fields),
    }
    response = requests.get(
        url,
        headers={"Authorization": f"Token {api_token}"},
        params=payload,
    )
    data = response.json()
    results = data["results"]

    # grab additional data if present NB: baserow returns the URL to the next
    # page as 'next' if there are further results or None so the while loop only
    # runs if there are further rows of data
    while data["next"]:
        response = requests.get(
            data["next"],
            headers={"Authorization": f"Token {api_token}"},
        )
        data = response.json()
        results = results + data["results"]

    if settings.VERBOSE:
        df = pd.DataFrame.from_records(results)
        print(df.head())

    return results


def get_bed_list(
    ward: str = "UCH T03 INTENSIVE CARE",
    table_id=BED_BONES_TABLE_ID,
    department_field_id=DEPARTMENT_FIELD_ID,
    fields=CORE_FIELDS,
    api_token=settings.BASEROW_READWRITE_TOKEN,
) -> list:
    """
    Queries the baserow API for a list of beds

    :returns:   Beds for this ward
    """

    url = f"{settings.BASEROW_URL}/api/database/rows/table/{table_id}/"

    if settings.VERBOSE:
        print(url)

    payload = {
        "user_field_names": "true",
        f"filter__field_{department_field_id}__equal": ward,
        "include": ",".join(fields),
    }
    response = requests.get(
        url,
        headers={"Authorization": f"Token {api_token}"},
        params=payload,
    )
    data = response.json()
    res = data["results"]

    if settings.VERBOSE:
        df = pd.DataFrame.from_records(res)
        print(df.head())

    return res


def update_bed_row(table_id=BED_BONES_TABLE_ID, row_id: int = None, data: dict = {}):
    """
    Updates a row in the beds table

    :param      table_id:  Table ID
    :param      row_id:  The row ID
    :param      data:  The data fields to update

    """

    url = f"{settings.BASEROW_URL}/api/database/rows/table/{table_id}/"

    requests.patch(
        url=f"{url}{row_id}/?user_field_names=true",
        headers={
            "Authorization": f"Token {settings.BASEROW_READWRITE_TOKEN}",
            "Content-Type": "application/json",
        },
        json=data,
    )


def unpack_nested_dict(
    rows: List[dict],
    f2unpack: str,
    subkey: str,
    new_name: str = "",
) -> List[dict]:
    """
    Unpack fields with nested dictionaries

    :param      rows:  The rows
    :param      f2unpack:  field to unpack
    :param      subkey:  key within nested dictionary to use
    :param      new_name: new name for field else overwrite if None

    :returns:   { description_of_the_return_value }
    """
    for row in rows:
        i2unpack = row.get(f2unpack, [])
        vals = [i.get(subkey, "") for i in i2unpack]
        vals_str = "|".join(vals)
        if new_name:
            row[new_name] = vals_str
        else:
            row.pop(f2unpack, None)
            row[f2unpack] = vals_str
    return rows