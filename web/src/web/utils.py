"""
Utility functions for web pages
"""
import numpy as np
import pandas as pd


def gen_id(name: str, dunder_name: str) -> str:
    module_name = dunder_name.split(".")[-2]
    name = name.replace("_", "-").replace(" ", "-").replace(".", "-")
    return f"{module_name}-{name}"


def time_since(when: pd.Series, units: str = "D") -> pd.Series:
    """
    Time since 'when' in units as per np.timedelta64
    e.g.  (D)ay, (M)onth, (Y)ear, (h)ours, (m)inutes,
    or (s)econds

    Accepts a pandas series
    Returns a float in the appropriate units
    defaults to days
    """
    try:
        res = (pd.Timestamp.now() - when.apply(pd.to_datetime)) / np.timedelta64(
            1, units
        )
    except TypeError as e:
        print(e)
        res = np.NaN
    return res


def unpack_nested_baserow_dict(
    rows: list[dict],
    f2unpack: str,
    subkey: str,
    new_name: str = "",
) -> list[dict]:
    # noinspection GrazieInspection,DuplicatedCode
    """
    Unpack fields with nested dictionaries into a pipe separated string

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
