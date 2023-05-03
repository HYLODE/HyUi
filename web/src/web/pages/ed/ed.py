import dash
from dash.dash_table import DataTable, FormatTemplate
import dash_bootstrap_components as dbc
import web.pages.ed.callbacks
from dash import html, dcc

dash.register_page(__name__, path="/ed_pred/", name="ED")


def layout() -> dbc.Container:
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
                            {"name": "Reverse Order", "id": "arrival_order"},
                            {"name": "Arrival Date", "id": "arrival_datetime_pretty"},
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
