from typing import Any

import requests
from dash import register_page, html, dcc, callback, Output, Input
from dash.dash_table import DataTable, FormatTemplate
from flask_login import current_user
import dash_bootstrap_components as dbc

from models.ed import EmergencyDepartmentPatient, AggregateAdmissionRow
from web.config import get_settings

register_page(__name__, name="ED Admissions")


def _get_individual_patients() -> list[EmergencyDepartmentPatient]:
    response = requests.get(f"{get_settings().api_url}/ed/individual/")
    return [EmergencyDepartmentPatient.parse_obj(row) for row in response.json()]


@callback(
    Output("individual-predictions-table", "data"),
    Input("title", "children"),
    background=True,
)
def individual_predictions_table(title: Any) -> Any:
    patients = _get_individual_patients()
    return [patient.dict() for patient in patients]


def _get_aggregations() -> list[AggregateAdmissionRow]:
    response = requests.get(f"{get_settings().api_url}/ed/aggregate/")
    return [AggregateAdmissionRow.parse_obj(row) for row in response.json()]


@callback(
    Output("beds-required", "data"),
    Input("title", "children"),
    background=True,
)
def beds_required(title: Any) -> Any:
    aggregations = _get_aggregations()
    return [aggregation.dict() for aggregation in aggregations]


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
            dbc.Row(dbc.Col(html.H2("Aggregate Predictions"))),
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
                            {
                                "name": "Beds Required >90% Confidence",
                                "id": "without_decision_to_admit_ninety_percent",
                            },
                            {
                                "name": "Beds Required >70% Confidence",
                                "id": "without_decision_to_admit_seventy_percent",
                            },
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
                            {"name": "Arrival Date", "id": "arrival_datetime"},
                            {"name": "Bed", "id": "bed"},
                            {"name": "MRN", "id": "mrn"},
                            {"name": "Name", "id": "name"},
                            {"name": "Sex", "id": "sex"},
                            {"name": "Date Of Birth", "id": "date_of_birth"},
                            {
                                "name": "Admission Likelihood",
                                "id": "admission_probability",
                                "type": "numeric",
                                "format": FormatTemplate.percentage(0),
                            },
                            {
                                "name": "Next Location",
                                "id": "next_location",
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
