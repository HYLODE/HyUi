from pathlib import Path

import pandas as pd

from .baserow import _add_table_field, _create_table


def _load_department_defaults() -> pd.DataFrame:
    df = pd.read_json(Path(__file__).parent / "department_defaults.json")
    df.fillna(
        value={
            "department_id": -1,
            "floor": -1,
            "capacity": -1,
        },
        inplace=True,
    )
    df["department_id"] = df["department_id"].astype(int)
    df["floor"] = df["floor"].astype(int)
    df["capacity"] = df["capacity"].astype(int)
    df["closed_perm_01"] = df["closed_perm_01"] == 1

    df = df[
        [
            "hl7_department",
            "department",
            "department_id",
            "floor",
            "floor_order",
            "closed_perm_01",
            "location_name",
            "department_external_name",
            "capacity",
        ]
    ]

    return df


def _create_departments_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    return _create_table(
        base_url,
        auth_token,
        application_id,
        "departments",
        "hl7_department",
        {},
        replace=True,
    )


def _add_departments_fields(base_url: str, auth_token: str, table_id: int) -> None:
    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="department_id",
        column_type="number",
        column_details={"number_negative": True},
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="floor",
        column_type="number",
        column_details={"number_negative": True},
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="floor_order",
        column_type="number",
        column_details={"number_negative": True},
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="capacity",
        column_type="number",
        column_details={"number_negative": True},
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="closed_perm_01",
        column_type="boolean",
        column_details=None,
    )

    text_cols = [
        "department",
        "clinical_service",
        "location_name",
        "department_external_name",
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
