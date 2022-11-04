"""
Methods for managing interaction with base row and beds bones
"""
from typing import List, Optional

from pydantic.main import BaseModel


class BedBonesBase(BaseModel):

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
