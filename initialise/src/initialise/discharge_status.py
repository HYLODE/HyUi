from .baserow import _add_table_field, _create_table


def _create_discharge_status_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    return _create_table(
        base_url,
        auth_token,
        application_id,
        "discharge_statuses",
        "csn",
        {},
    )


def _add_discharge_status_fields(base_url: str, auth_token: str, table_id: int) -> None:
    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="status",
        column_type="text",
        column_details=None,
    )

    _add_table_field(
        base_url,
        auth_token,
        table_id,
        column_name="modified_at",
        column_type="date",
        column_details={
            "date_format": "ISO",
            "date_include_time": True,
            "date_time_format": "24",
        },
    )
