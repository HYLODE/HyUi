from dash import Input, Output, callback

from web.pages.electives import ids
from web.stores import ids as store_ids
from datetime import date, timedelta


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

    if campus != []:
        electives = [
            row for row in electives if campus_dict[campus] in row["department_name"]
        ]

    if date is not None:
        electives = [row for row in electives if row["surgery_date"] == date]

    for row in electives:
        row["full_name"] = row["first_name"] + " " + row["last_name"]
        row["age_sex"] = str(row["age_in_years"]) + row["sex"][:1]

    return electives


@callback(Output("date_selected", "data"), Input("date_selected", "value"))
def _get_date(value: date) -> list[dict]:
    return [
        {
            "value": date.today(),
            "label": date.today().strftime("%A %d"),
        },
        {
            "value": (date.today() + timedelta(days=1)),
            "label": (date.today() + timedelta(days=1)).strftime("%A %d"),
        },
        {
            "value": (date.today() + timedelta(days=2)),
            "label": (date.today() + timedelta(days=2)).strftime("%A %d"),
        },
    ]


@callback(
    Output("patient_info_box", "children"),
    Input(ids.ELECTIVES_TABLE, "data"),
    Input(ids.ELECTIVES_TABLE, "active_cell"),
    Input(store_ids.ELECTIVES_STORE, "data"),
)
def _make_info_box(
    current_table: list[dict], active_cell: dict, electives: list[dict]
) -> str:

    string = ""
    if active_cell is not None:
        patient_mrn = current_table[active_cell["row"]]["primary_mrn"]
        pt = [row for row in electives if row["primary_mrn"] == patient_mrn][0]
        # could make a table? [{k: v} for (k, v) in all_patient_info[0].items()]

        string = f""" FURTHER INFORMATION
MRN: {pt['primary_mrn']}
PACU: {pt['pacu']}.
Name: {pt['first_name']} {pt['last_name']}
Age: {pt['age_in_years']} {pt['sex']}
Operation:
{pt['patient_friendly_name']}

Echocardiography:
Patient has had {pt['num_echo']} echos,
of which {pt['abnormal_echo']} were abnormal.
Last echo: [will pull narrative here]

Preassessment date: {pt['preassess_date']}:
ASA: {pt['asa']}
Our system has provided the following risk scores:
    Cardio: {pt['cardio']}
[etc]

Recent bloods and obs:
Number of abnormal CRPs: {pt['crp_abnormal_count']}
Maximum BMI: {pt['bmi_max_value']}

Booked destination: {pt['booked_destination']}
Protocolised Admission: {pt['protocolised_adm']}

Probability of ICU admission by our model:

        """
    return string
