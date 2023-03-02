from dash import Input, Output, callback

from web.pages.electives import ids, CAMPUSES
from web.stores import ids as store_ids

import textwrap
from datetime import datetime


@callback(
    Output(ids.ELECTIVES_TABLE, "data"),
    Output(ids.ELECTIVES_TABLE, "filter_query"),
    Input(ids.CAMPUS_SELECTOR, "value"),
    Input(store_ids.ELECTIVES_STORE, "data"),
    Input("date_selector", "value"),
    Input("pacu_selector", "value"),
)
def _store_electives(
    campus: str, electives: list[dict], date: str, pacu_selection: bool
) -> tuple[list[dict], str]:

    icu_cut_off = 0.5
    preassess_date_cut_off = 90

    campus_dict = {i.get("value"): i.get("label") for i in CAMPUSES}
    electives = [
        row
        for row in electives
        if campus_dict.get(campus, "") in row["department_name"]
    ]

    if date is not None:
        electives = [
            row
            for row in electives
            if row["surgery_date"] >= date[0] and row["surgery_date"] <= date[1]
        ]

    i = 0
    for row in electives:
        row["id"] = i
        i += 1

        row["full_name"] = "{first_name} {last_name}".format(**row)
        row["age_sex"] = "{age_in_years}{sex[0]}".format(**row)

        row["pacu_yn"] = (
            "✅ BOOKED"
            if row["pacu"] and row["icu_prob"] > icu_cut_off
            else "✅ BOOKED"  # "✅🤷BOOKED"
            if row["pacu"] and row["icu_prob"] < icu_cut_off
            else "⚠️Not booked"
            if not row["pacu"] and row["icu_prob"] > icu_cut_off
            else "❌ Not booked"
        )
        row["preassess_status"] = (
            f"⚠️{row['preassess_date']}"
            if (
                datetime.strptime(row["surgery_date"], "%Y-%m-%d").date()
                - datetime.strptime(row["preassess_date"], "%Y-%m-%d").date()
            ).days
            > preassess_date_cut_off
            else f"✅{row['preassess_date']}"
            if row["pac_nursing_outcome"] in ("OK to proceed", "Fit for surgery")
            else f"⚠️{row['preassess_date']}"
            if row["pac_nursing_outcome"]
            in (
                "Referred to anaesthetist",
                "Yes",
                "Further tests / optimisation required",
                "Not fit for surgery",
            )
            and row["pac_dr_review"] is None
            else f"✅{row['preassess_date']}"
        )

    filter_query = (
        f"{{pacu_yn}} scontains {pacu_selection}" if pacu_selection is not None else ""
    )

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
    info_box_width = 65

    if active_cell is None:
        patient_mrn = current_table[0]["primary_mrn"]
    else:
        patient_mrn = current_table[active_cell["row_id"]]["primary_mrn"]
    pt = [row for row in electives if row["primary_mrn"] == patient_mrn][0]

    string = """FURTHER INFORMATION
Name: {first_name} {last_name}, {age_in_years}{sex[0]}
MRN: {primary_mrn}
Operation: {patient_friendly_name}
PACU: {pacu}

Original surgical booking destination: {booked_destination}
Protocolised Admission: {protocolised_adm}

Medical History: {display_string}
Maximum BMI: {bmi_max_value}.


Echocardiography:
Patient has had {num_echo} echos,
of which {abnormal_echo} were flagged as abnormal.
Last echo ({last_echo_date}): {last_echo_narrative}


Preassessment date: {preassess_date}.
Destination on preassessment clinic booking: {pacdest}
Nursing outcome: {pac_nursing_outcome}
Anaesthetic review: {pac_dr_review}
Nursing issues: {pac_nursing_issues}

""".format(
        **pt
    )

    return "\n".join([textwrap.fill(x, info_box_width) for x in string.split("\n")])
