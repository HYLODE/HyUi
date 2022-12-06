from dash import Input, Output, callback

from web.pages.electives import ids
from web.stores import ids as store_ids


@callback(
    Output(ids.ELECTIVES_TABLE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.ELECTIVES_STORE, "data"),
)
def _store_electives(campus: str, electives: list[dict]) -> list[dict]:
    # try:
    #     these_depts = [dept for dept in depts if dept.get("location_name")
    #     == campus]
    # except TypeError as e:
    #     print(e)
    #     warnings.warn(f"No departments found at {campus} campus")
    #     these_depts = []
    return electives
