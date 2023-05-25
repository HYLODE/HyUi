# type: ignore
from typing import Any, Dict, List

from dash import Input, Output, callback

from models.ed import AggregateAdmissionRow, EmergencyDepartmentPatient
from web import API_URLS
from web import ids as app_ids
from web.celery_tasks import requests_try_cache
from web.convert import parse_to_data_frame
from web.logger import logger_timeit
from web.pages.ed import ids
from web.style import colors


# if the time is in utc:
ts_obj = "d3.timeParse('%Y-%m-%dT%H:%M:%S%Z')(params.data.arrival_datetime)"

cellStyle_pAdmission = {
    "styleConditions": [
        {
            "condition": "params.value >.75",
            "style": {"backgroundColor": colors.red},
        },
        {
            "condition": "params.value >.50",
            "style": {"backgroundColor": colors.orange},
        },
        {
            "condition": "params.value >.25",
            "style": {"backgroundColor": colors.yellow},
        },
        {
            "condition": "params.value <=.25",
            "style": {"backgroundColor": colors.white},
        },
    ]
}
columnDefs_patients = [
    {
        "headerName": "Arrived",
        "field": "arrival_datetime",
        "valueGetter": {"function": ts_obj},
        "valueFormatter": {"function": f"d3.timeFormat('%H:%M %a %e')({ts_obj})"},
    },
    {
        "headerName": "Location",
        "field": "bed",
    },
    {
        "headerName": "MRN",
        "field": "mrn",
    },
    {
        "headerName": "Name",
        "field": "name",
    },
    {
        "headerName": "Sex",
        "field": "sex",
    },
    {
        "headerName": "DoB",
        "field": "date_of_birth",
    },
    {
        "headerName": "P(Admission)",
        "field": "admission_probability",
        "valueFormatter": {"function": "d3.format(',.0%')(params.value)"},
        "cellStyle": cellStyle_pAdmission,
        # "cellRenderer": "DBC_Button_Simple",
        # "cellRendererParams": {"color": "success"},
    },
    {
        "headerName": "Destination",
        "field": "next_location",
    },
]


@logger_timeit()
def _get_aggregate_patients() -> list[AggregateAdmissionRow]:
    url = API_URLS[ids.AGGREGATE_STORE]
    data = requests_try_cache(url)
    return [AggregateAdmissionRow.parse_obj(row).dict() for row in data]


@callback(
    Output(ids.AGGREGATE_STORE, "data"),
    Input(app_ids.STORE_TIMER_15M, "n_intervals"),
)
def store_aggregate_patients(n_intervals: int) -> List[Dict[str, Any]]:
    if n_intervals >= 0:
        return _get_aggregate_patients()


@logger_timeit()
def _get_individual_patients() -> list[EmergencyDepartmentPatient]:
    url = API_URLS[ids.PATIENTS_STORE]
    data = requests_try_cache(url)
    return [EmergencyDepartmentPatient.parse_obj(row).dict() for row in data]


@callback(
    Output(ids.PATIENTS_STORE, "data"),
    Input(app_ids.STORE_TIMER_15M, "n_intervals"),
)
def store_individual_patients(n_intervals: int) -> List[Dict[str, Any]]:
    if n_intervals >= 0:
        return _get_individual_patients()


@callback(
    Output(ids.PATIENTS_GRID, "rowData"),
    Output(ids.PATIENTS_GRID, "columnDefs"),
    Input(ids.PATIENTS_STORE, "data"),
)
def build_patients_grid(data):
    df = parse_to_data_frame(data, EmergencyDepartmentPatient)
    columnDefs = columnDefs_patients
    return df.to_dict("records"), columnDefs
