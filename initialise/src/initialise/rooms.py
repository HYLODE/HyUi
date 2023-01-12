from pathlib import Path
import pandas as pd
from .baserow import _add_table_field, _create_table


def _load_room_defaults() -> pd.DataFrame:
    df = pd.read_json(Path(__file__).parent / "room_defaults.json")
    df.fillna(
        value={
            "room_id": -1,
        },
        inplace=True,
    )
    df["room_id"] = df["room_id"].astype(int)

    df = df[
        [
            "room",
            "room_id",
            "hl7_room",
            "department",
            "has_beds",
            "is_sideroom",
        ]
    ]

    return df


def _create_rooms_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    return _create_table(
        base_url,
        auth_token,
        application_id,
        "rooms",
        "hl7_room",
        {},
        replace=True,
    )


def _add_rooms_fields(base_url: str, auth_token: str, table_id: int) -> None:
    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="room_id",
        column_type="number",
        column_details={"number_negative": True},
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="is_sideroom",
        column_type="boolean",
        column_details=None,
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="has_beds",
        column_type="boolean",
        column_details=None,
    )

    text_cols = [
        "room",
        "department",
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
