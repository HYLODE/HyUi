from dash import Input, Output, callback

from web.pages.electives import ids
from web.stores import ids as store_ids


@callback(
    Output(ids.ELECTIVES_TABLE, "data"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.ELECTIVES_STORE, "data"),
    Input("date_selected", "value"),
)
def _store_electives(campus: str, electives: list[dict], date: str) -> list[dict]:
    # model_rows = (MergedData.parse_obj(row) for row in electives)
    # df = pd.DataFrame.from_records(
    #     (row.dict() for row in model_rows), columns=MergedData.__fields__.keys()
    # )

    # I am not sure how to get the "label" rather than the "value" from "CAMPUS";
    # I have trundled around this without elegance.

    campus_dict = {
        "UNIVERSITY COLLEGE HOSPITAL CAMPUS": "UCH",
        "GRAFTON WAY BUILDING": "GWB",
        "WESTMORELAND STREET": "WMS",
        "QUEEN SQUARE CAMPUS": "NHNN",
    }
    # filter by campus
    campus_electives = [
        row for row in electives if campus_dict[campus] in row["department_name"]
    ]

    # then filter by date selected
    elective_table = [row for row in campus_electives if date == row["surgery_date"]]

    print(elective_table)
    return elective_table
