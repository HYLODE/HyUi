import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash.dash_table import DataTable, FormatTemplate

dash.register_page(__name__, path="/ed/table", name="ED")

from datetime import datetime
from typing import Any, Dict, List

from dash import Input, Output, callback

from models.ed import AggregateAdmissionRow, EmergencyDepartmentPatient
from web.celery_tasks import requests_try_cache
from web.config import get_settings
from web.convert import parse_to_data_frame
from web.logger import logger, logger_timeit
from web import ids as app_ids
from web.pages.ed import ids

logger.debug("Confirm that you have imported all the callbacks")


# arrival_datetime"2022-10-12T13:14:00"
# bed"BED2"
# mrn"MRNABC1"
# name"Donald Trump"
# sex"F"
# date_of_birth"1990-10-06"
# admission_probability0.06
# next_locationnull

columnDefs_patients = [
    {
        "headerName": "Arrived",
        "field": "arrival_datetime",
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
        # "cellRenderer": "DBC_Button_Simple",
        # "cellRendererParams": {"color": "success"},
    },
    {
        "headerName": "Destination",
        "field": "next_location",
    },
]


@logger_timeit()
def _get_individual_patients() -> list[EmergencyDepartmentPatient]:
    # response = requests.get(f"{get_settings().api_url}/ed/individual/")
    url = f"{get_settings().api_url}/ed/individual/"
    data, response_code = requests_try_cache(url)
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


grid = dag.AgGrid(
    id=ids.PATIENTS_GRID,
    columnSize="responsiveSizeToFit",
    defaultColDef={
        # "autoSize": True,
        "resizable": True,
        "sortable": True,
        "filter": True,
        # "minWidth": 100,
        # "responsiveSizeToFit": True,
        # "columnSize": "sizeToFit",
    },
    className="ag-theme-material",
)

timers = html.Div(
    [
        # dcc.Interval(
        #     id=ids.ED_TIMER,
        #     interval=15 * 60 * 1000,
        #     n_intervals=0,
        # ),
    ]
)

stores = html.Div(
    [
        dcc.Store(id=ids.PATIENTS_STORE),
    ]
)
notifications = html.Div(
    [
        # html.Div(id=ids.ACC_BED_SUBMIT_WARD_NOTIFY),
    ]
)

body = dmc.Container(
    [
        dmc.Grid(
            children=[
                dmc.Col(grid, span=12),
            ],
        ),
    ],
    style={"width": "100vw"},
    fluid=True,
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            notifications,
            body,
            # inspector,
        ]
    )


# @logger_timeit()
# def _get_aggregations() -> list[AggregateAdmissionRow]:
#     # response = requests.get(f"{get_settings().api_url}/ed/aggregate/")
#     url = f"{get_settings().api_url}/ed/aggregate/"
#     data, response_code = requests_try_cache(url)
#     return [AggregateAdmissionRow.parse_obj(row) for row in data]


# def _prettify_datetime(s: datetime) -> str:
#     """Private method to format string"""
#     return s.strftime("%H:%M %a %d %b")


# @callback(
#     Output("individual-predictions-table", "data"),
#     Input("title", "children"),
#     background=True,
# )
# def individual_predictions_table(title: Any) -> List[Dict]:
#     patients = _get_individual_patients()
#     ps = [patient.dict() for patient in patients]
#     ps = sorted(ps, key=lambda i: i["arrival_datetime"], reverse=True)  # type: ignore
#     for i, p in enumerate(ps):
#         p["arrival_datetime_pretty"] = _prettify_datetime(p["arrival_datetime"])
#         p["arrival_order"] = i + 1  # most recent patient = 1
#     return ps


# @callback(
#     Output("beds-required", "data"),
#     Input("title", "children"),
#     background=True,
# )
# def beds_required(title: Any) -> Any:
#     aggregations = _get_aggregations()
#     return [aggregation.dict() for aggregation in aggregations]


# def layout() -> dbc.Container:
#     return dbc.Container(
#         [
#             dbc.Row(
#                 dbc.Col(
#                     html.H1(
#                         id="title",
#                         children="A&E Admission Predictions",
#                     )
#                 )
#             ),
#             dbc.Row(dbc.Col(html.H2("Aggregate Predictions"))),
#             dbc.Row(
#                 dbc.Col(
#                     """
#             Of the current patients in ED that do not have decisions to admit we
#             predict the following numbers of beds will be required:
#             """
#                 )
#             ),
#             dbc.Row(
#                 dbc.Col(
#                     DataTable(
#                         id="beds-required",
#                         data=[],
#                         columns=[
#                             {"name": "Speciality", "id": "speciality"},
#                             {
#                                 "name": "Beds Required >90% Confidence",
#                                 "id": "without_decision_to_admit_ninety_percent",
#                             },
#                             {
#                                 "name": "Beds Required >70% Confidence",
#                                 "id": "without_decision_to_admit_seventy_percent",
#                             },
#                         ],
#                     )
#                 )
#             ),
#             dbc.Row(dbc.Col(html.H2("Individual Predictions"))),
#             dbc.Row(
#                 dbc.Col(
#                     DataTable(
#                         id="individual-predictions-table",
#                         data=[],
#                         columns=[
#                             {"name": "Reverse Order", "id": "arrival_order"},
#                             {"name": "Arrival Date", "id": "arrival_datetime_pretty"},
#                             {"name": "Bed", "id": "bed"},
#                             {"name": "MRN", "id": "mrn"},
#                             {"name": "Name", "id": "name"},
#                             {"name": "Sex", "id": "sex"},
#                             {"name": "Date Of Birth", "id": "date_of_birth"},
#                             {
#                                 "name": "Admission Likelihood",
#                                 "id": "admission_probability",
#                                 "type": "numeric",
#                                 "format": FormatTemplate.percentage(0),
#                             },
#                             {
#                                 "name": "Next Location",
#                                 "id": "next_location",
#                             },
#                         ],
#                         sort_action="native",
#                         sort_mode="multi",
#                         style_data_conditional=[
#                             {
#                                 "if": {
#                                     "column_id": "prediction_as_real",
#                                     "filter_query": (
#                                         f"{{prediction_as_real}} >= {c / 10} "
#                                         f"&& {{prediction_as_real}} < {c / 10 + 0.1}"
#                                     ),
#                                 },
#                                 "backgroundColor": f"rgba(255, 65, 54, {c / 10})",
#                             }
#                             for c in range(0, 11)
#                         ],
#                     )
#                 )
#             ),
#             dcc.Store(id="individual-data"),
#         ],
#         fluid=True,
#     )
