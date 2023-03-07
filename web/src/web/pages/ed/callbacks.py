from typing import Any, List, Dict
from web.config import get_settings

from datetime import datetime
import requests
from dash import callback, Output, Input

from models.ed import EmergencyDepartmentPatient, AggregateAdmissionRow


def _get_individual_patients() -> list[EmergencyDepartmentPatient]:
    response = requests.get(f"{get_settings().api_url}/ed/individual/")
    return [EmergencyDepartmentPatient.parse_obj(row) for row in response.json()]


def _get_aggregations() -> list[AggregateAdmissionRow]:
    response = requests.get(f"{get_settings().api_url}/ed/aggregate/")
    return [AggregateAdmissionRow.parse_obj(row) for row in response.json()]


def _prettify_datetime(s: datetime) -> str:
    """Private method to format string"""
    return s.strftime("%H:%M %a %d %b")


@callback(
    Output("individual-predictions-table", "data"),
    Input("title", "children"),
    background=True,
)
def individual_predictions_table(title: Any) -> List[Dict]:
    patients = _get_individual_patients()
    ps = [patient.dict() for patient in patients]
    ps = sorted(ps, key=lambda i: i["arrival_datetime"], reverse=True)  # type: ignore
    for i, p in enumerate(ps):
        p["arrival_datetime_pretty"] = _prettify_datetime(p["arrival_datetime"])
        p["arrival_order"] = i + 1  # most recent patient = 1
    return ps


@callback(
    Output("beds-required", "data"),
    Input("title", "children"),
    background=True,
)
def beds_required(title: Any) -> Any:
    aggregations = _get_aggregations()
    return [aggregation.dict() for aggregation in aggregations]
