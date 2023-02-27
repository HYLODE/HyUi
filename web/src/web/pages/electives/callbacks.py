from dash import Input, Output, callback

from web.pages.electives import ids, CAMPUSES
from web.stores import ids as store_ids

import textwrap


@callback(
    Output(ids.ELECTIVES_TABLE, "data"),
    Output(ids.ELECTIVES_TABLE, "filter_query"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.ELECTIVES_STORE, "data"),
    Input("date_selected", "value"),
    Input("pacu_selector", "value"),
)
def _store_electives(
    campus: str, electives: list[dict], date: str, pacu_selection: bool
) -> tuple[list[dict], str]:
    campus_dict = {i.get("value"): i.get("label") for i in CAMPUSES}

    if campus != []:
        electives = [
            row for row in electives if campus_dict[campus] in row["department_name"]
        ]

    if date is not None:
        electives = [
            row
            for row in electives
            if row["surgery_date"] >= date[0] and row["surgery_date"] <= date[1]
        ]

    i = 0

    for row in electives:
        row["full_name"] = "{first_name} {last_name}".format(**row)
        row["age_sex"] = "{age_in_years}{sex[0]}".format(**row)
        row["id"] = i  # this is a row_id for the //current table// only
        i += 1

    if pacu_selection is not None:
        filter_query = f"{{pacu}} scontains {pacu_selection}"
    return electives, filter_query


@callback(
    Output("patient_info_box", "children"),
    Input(ids.ELECTIVES_TABLE, "data"),
    Input(ids.ELECTIVES_TABLE, "active_cell"),
    Input(store_ids.ELECTIVES_STORE, "data"),
)
def _make_info_box(
    current_table: list[dict], active_cell: dict, electives: list[dict]
) -> str:
    """
    Outputs text for the patient_info_box.
    If no cell is selected, automatically first patient.
    info_box_width is number of characters.
    """
    info_box_width = 55

    if active_cell is None:
        patient_mrn = current_table[0]["primary_mrn"]
    else:
        patient_mrn = current_table[active_cell["row_id"]]["primary_mrn"]
    pt = [row for row in electives if row["primary_mrn"] == patient_mrn][0]
    # could make a table? [{k: v} for (k, v) in all_patient_info[0].items()]

    string = """FURTHER INFORMATION
Name: {first_name} {last_name}, {age_in_years}{sex[0]}
MRN: {primary_mrn}
Operation: {patient_friendly_name}
PACU: {pacu}

Original surgical booking destination: {booked_destination}
Protocolised Admission: {protocolised_adm}

Echocardiography:
Patient has had {num_echo} echos,
of which {abnormal_echo} were flagged as abnormal.
Last echo ({last_echo_date}): {last_echo_narrative}

Preassessment date: {preassess_date}:
ASA: {asa}. Maximum BMI: {bmi_max_value}.
Destination on preassessment clinic booking: {pacdest}
Preassessment summary: {pa_summary}
""".format(
        **pt
    )

    return "\n".join([textwrap.fill(x, info_box_width) for x in string.split("\n")])
