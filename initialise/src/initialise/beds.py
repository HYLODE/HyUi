"""
Prepare beds table
"""
from pathlib import Path

import pandas as pd

from initialise.baserow import _add_table_field, _create_table


def _create_bed_bones_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    """Create the beds table derived from epic and emap merge"""
    return _create_table(
        base_url, auth_token, application_id, "beds_bones", "location", {}, replace=True
    )


def _load_beds_user_defaults(json_file_path: Path) -> pd.DataFrame:
    df = pd.read_json(json_file_path)
    df.fillna(
        value={
            # fill na with -1 since json will convert integers to float
            # otherwise
            "location_id": -1,
            "department_id": -1,
            "room_id": -1,
            "bed_id": -1,
            "bed_index": -1,
            "xpos": -1,
            "ypos": -1,
            # bool
            "closed": False,
        },
        inplace=True,
    )
    df["xpos"] = df["xpos"].astype(int)
    df["ypos"] = df["ypos"].astype(int)

    return df


def _create_beds_user_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    """Create the user configurable beds table"""
    return _create_table(
        base_url,
        auth_token,
        application_id,
        "beds",
        "location_string",
        {},
        replace=True,
    )


def _add_beds_user_fields(base_url: str, auth_token: str, table_id: int) -> None:
    text_cols = [
        "location_name",
        "department",
        "room",
        "hl7_bed",
        "hl7_room",
        "hl7_department",
    ]
    for col in text_cols:
        _add_table_field(
            base_url,
            auth_token,
            table_id,
            column_name=col,
            column_type="text",
            column_details=None,
        )

    integer_cols = [
        "location_id",
        "department_id",
        "room_id",
        "bed_id",
        "bed_number",
        "floor",
        "bed_index",
        "xpos",
        "ypos",
    ]
    for col in integer_cols:
        _add_table_field(
            base_url,
            auth_token,
            table_id,
            column_name=col,
            column_type="number",
            column_details={"number_negative": True},
        )

    _add_table_field(base_url, auth_token, table_id, "closed", "boolean", {})
    _add_table_field(base_url, auth_token, table_id, "blocked", "boolean", {})
    _add_table_field(base_url, auth_token, table_id, "covid", "boolean", {})

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="bed_physical",
        column_type="multiple_select",
        column_details={
            "select_options": [
                (1, "sideroom", "red"),
                (2, "ventilator", "red"),
                (3, "monitored", "red"),
                (4, "ensuite", "red"),
                (5, "virtual", "red"),
            ]
        },
    )
    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="bed_functional",
        column_type="multiple_select",
        column_details={
            "select_options": [
                (1, "periop", "red"),
                (2, "ficm", "red"),
                (3, "gwb", "red"),
                (4, "wms", "red"),
                (5, "t06", "red"),
                (6, "north", "red"),
                (7, "south", "red"),
                (8, "plex", "red"),
                (9, "nhnn", "red"),
                (10, "hdu", "red"),
                (11, "icu", "red"),
            ]
        },
    )
