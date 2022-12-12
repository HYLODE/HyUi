"""
Utility functions for web pages
"""


def unpack_nested_baserow_dict(
    rows: list[dict],
    f2unpack: str,
    subkey: str,
    new_name: str = "",
) -> list[dict]:
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
