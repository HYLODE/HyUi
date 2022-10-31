from typing import Any

import pandas as pd
from dash import register_page, html, dcc, callback, Output, Input
from dash.dash_table import DataTable, FormatTemplate
from flask_login import current_user
import dash_bootstrap_components as dbc

register_page(__name__, name="ED Admissions")


@callback(
    Output("patient-count", "children"),
    Input("individual-data", "data"),
)
def patient_count(census_data: Any) -> str:
    count = 2
    return f"Patients in the department: {count}."


@callback(
    Output("decision-to-admit-count", "children"),
    Input("individual-data", "data"),
)
def decision_to_admit_count(census_data: Any) -> str:
    count = 3
    return f"Patients with decisions to admit: {count}."


@callback(
    Output("individual-data", "data"),
    Input("title", "children"),  # Inconsequential input.
)
def individual_predictions_data(previous_data: Any) -> Any:

    return []


@callback(
    Output("individual-predictions-table", "data"),
    Input("individual-data", "data"),
)
def individual_predictions_table(census_data: Any) -> Any:
    return pd.DataFrame(
        [
            {
                "admission_dt_str": "20221020 12:00",
                "bed_code": "bed code",
                "mrn": "mrn",
                "sex": "sex",
                "dob_str": "dob",
                "prediction_as_real": 0.5,
                "decision_to_admit_str": "decision",
            }
        ]
    ).to_dict("records")


@callback(
    Output("beds-required", "data"),
    Input("individual-data", "data"),
)
def beds_required(census_data: Any) -> Any:
    specialities = ["medical", "surgical", "haem_onc", "paediatric", "other"]

    return pd.DataFrame(
        {
            "speciality": specialities,
            "ninety": [1, 2, 3, 4, 5],
            "seventy": [1, 2, 3, 4, 5],
        }
    ).to_dict("records")


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])

    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.H1(
                        id="title",
                        children="Emergency Department Admission Predictions",
                    )
                )
            ),
            dbc.Row(dbc.Col(html.H2("Overview"))),
            dbc.Row(dbc.Col(id="patient-count")),
            dbc.Row(dbc.Col(id="decision-to-admit-count")),
            dbc.Row(dbc.Col(html.H2("Predicted Admissions"))),
            dbc.Row(
                dbc.Col(
                    """
            Of the current patients in ED that do not have decisions to admit we
            predict the following numbers of beds will be required:
            """
                )
            ),
            dbc.Row(
                dbc.Col(
                    DataTable(
                        id="beds-required",
                        data=[],
                        columns=[
                            {"name": "Speciality", "id": "speciality"},
                            {"name": "Beds Required >90% Confidence", "id": "ninety"},
                            {"name": "Beds Required >70% Confidence", "id": "seventy"},
                        ],
                    )
                )
            ),
            dbc.Row(dbc.Col(html.H2("Individual Predictions"))),
            dbc.Row(
                dbc.Col(
                    DataTable(
                        id="individual-predictions-table",
                        data=[],
                        columns=[
                            {"name": "Arrival Date", "id": "admission_dt_str"},
                            {"name": "Bed", "id": "bed_code"},
                            {"name": "MRN", "id": "mrn"},
                            {"name": "Name", "id": "name"},
                            {"name": "Sex", "id": "sex"},
                            {"name": "Date Of Birth", "id": "dob_str"},
                            {
                                "name": "Admission Likelihood",
                                "id": "prediction_as_real",
                                "type": "numeric",
                                "format": FormatTemplate.percentage(0),
                            },
                            {
                                "name": "Decision To Admit?",
                                "id": "decision_to_admit_str",
                            },
                        ],
                        sort_action="native",
                        sort_mode="multi",
                        style_data_conditional=[
                            {
                                "if": {
                                    "column_id": "prediction_as_real",
                                    "filter_query": (
                                        f"{{prediction_as_real}} >= {c / 10} "
                                        f"&& {{prediction_as_real}} < {c / 10 + 0.1}"
                                    ),
                                },
                                "backgroundColor": f"rgba(255, 65, 54, {c / 10})",
                            }
                            for c in range(0, 11)
                        ],
                    )
                )
            ),
            dcc.Store(id="individual-data"),
        ],
        fluid=True,
    )