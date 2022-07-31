# src/utils/beds.py
"""
Methods for managing interaction with base row and beds bones
"""
import pandas as pd
import requests

from typing import List
from config.settings import settings
from utils.wards import wards

from typing import Optional
from sqlmodel import SQLModel

class BedBonesBase(SQLModel):

    id: int
    order: float
    department: str
    room: str
    bed: str
    unit_order: Optional[str]
    closed: Optional[bool]
    covid: Optional[bool]
    bed_functional: Optional[str]
    bed_physical: Optional[str]



BED_BONES_TABLE_ID = 261
DEPARTMENT_FIELD_ID = 2041
CORE_FIELDS = [
    "department",
    "room",
    "bed",
    "unit_order",
    "closed",
    "covid",
    "bed_functional",
    "bed_physical",
]


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


