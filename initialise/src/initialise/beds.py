"""
Prepare beds table
"""
from .baserow import _add_table_field, _create_table


# Create the beds table.
def _create_beds_table(
    base_url: str,
    auth_token: str,
    application_id: int,
) -> int:
    return _create_table(base_url, auth_token, application_id, "beds", "location", {})


def _add_beds_fields(base_url: str, auth_token: str, table_id: int) -> None:
    _add_table_field(base_url, auth_token, table_id, "closed", "boolean", {})
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
