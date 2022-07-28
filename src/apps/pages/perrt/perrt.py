# src/apps/perrt/perrt.py
"""
sub-application for perrt
"""


import dash_bootstrap_components as dbc
import plotly.express as px
from dash import Input, Output, callback, register_page
from dash import dash_table as dt
from dash import dcc, html
from pydantic import parse_obj_as

from config.settings import settings
from utils import get_model_from_route
from utils.dash import get_results_response, df_from_store

register_page(__name__)
BPID = "PERRT_"
PerrtRead = get_model_from_route("Perrt", "Read")

API_URL = f"{settings.API_URL}/perrt/"
ADMISSION_PREDICTION_URL = f"{API_URL}admission_predictions"

REFRESH_INTERVAL = 10 * 60 * 1000  # milliseconds

card_fig = dbc.Card(
    [
        # dbc.CardHeader(html.H6("Ward patients")),
        dbc.CardBody(
            [
                html.Div([html.P("UCLH inpatients and vital signs (Tower)")]),
                fig_perrt := html.Div(),
            ]
        ),
    ]
)

card_table = dbc.Card(
    [
        # dbc.CardHeader(html.H6("Ward patients")),
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.P(
                            "Inpatients sorted by highest NEWS score in the last 12 hours"
                        )
                    ]
                ),
                table_perrt := html.Div(),
            ]
        ),
    ]
)

main = html.Div(
    [
        card_fig,
        card_table,
    ]
)


dash_only = html.Div(
    [
        query_interval := dcc.Interval(interval=REFRESH_INTERVAL, n_intervals=0),
        request_data := dcc.Store(id=f"{BPID}request_data"),
    ]
)

layout = html.Div(
    [
        main,
        dash_only,
    ],
)


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
def store_data(n_intervals: int) -> dict:
    """
    Read data from API then store as JSON
    """
    data = [dict(parse_obj_as(PerrtRead, i)) for i in get_results_response(API_URL)]

    hospital_visit_ids = [x['hospital_visit_id'] for x in data]
    
    predictions_list = get_results_response(ADMISSION_PREDICTION_URL, "POST", hospital_visit_ids)
    predictions = {x['hospital_visit_id'] : x['admission_probability'] for x in predictions_list}

    l = list()

    for entry in data:
        entry["admission_probability"] = predictions.get(str(entry['hospital_visit_id']), 0.0)
        l.append(entry)

    return l


@callback(
    Output(fig_perrt, "children"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def gen_simple_fig(data: dict):
    # TODO: move data validation to store
    df = df_from_store(data, PerrtRead)
    df = df[["dept_name", "news_scale_1_max", "mrn"]]
    df = df.groupby(["dept_name", "news_scale_1_max"], as_index=False).count()
    fig = px.bar(df, x="dept_name", y="mrn", color="news_scale_1_max")
    return dcc.Graph(id="perrt_fig", figure=fig)


@callback(
    Output(table_perrt, "children"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def gen_simple_table(data: dict):
    # TODO: reintroduce data validation
    # ideally this should happen when storing

    cols = dict(
        mrn="MRN",
        lastname="Last name",
        firstname="First name",
        date_of_birth="DoB",
        dept_name="Ward/Department",
        bed_hl7="Bed",
        perrt_consult_datetime="PERRT consult",
        news_scale_1_max="NEWS (max)",
        news_scale_1_min="NEWS (min)",
        admission_probability="Admission probability",
    )
    return [
        dt.DataTable(
            id="results_table",
            columns=[{"name": v, "id": k} for k, v in cols.items()],
            data=data,
            filter_action="native",
            sort_action="native",
            page_current=0,
            page_size=10,
            # export_format="xlsx",
            # export_headers="display",
        )
    ]
