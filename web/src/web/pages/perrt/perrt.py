import json

import dash_bootstrap_components as dbc
import plotly.express as px
import requests
from dash import Input, Output, callback, register_page, get_app
from dash import dash_table as dt
from dash import dcc, html
from flask_caching import Cache
from flask_login import current_user

from models.perrt import EmapVitalsLong, EmapVitalsWide
from web.config import get_settings
from web.convert import parse_to_data_frame

CACHE_TIMEOUT = 5 * 60 * 1000
BPID = "PERRT_"

register_page(__name__)
app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)

REFRESH_INTERVAL = 10 * 60 * 1000  # milliseconds

NEWS_SCORE_COLORS = {
    "1": "rgb(189, 230, 175)",
    "2": "rgb(189, 230, 175)",
    "3": "rgb(189, 230, 175)",
    "4": "rgb(189, 230, 175)",
    "5": "rgb(247, 215, 172)",
    "6": "rgb(247, 215, 172)",
    "7": "rgb(240, 158, 158)",
    "8": "rgb(240, 158, 158)",
    "9": "rgb(240, 158, 158)",
    "10": "rgb(240, 158, 158)",
    "11": "rgb(240, 158, 158)",
    "12": "rgb(240, 158, 158)",
    "13": "rgb(240, 158, 158)",
    "14": "rgb(240, 158, 158)",
    "15": "rgb(240, 158, 158)",
    "16": "rgb(240, 158, 158)",
    "17": "rgb(240, 158, 158)",
    "18": "rgb(240, 158, 158)",
    "19": "rgb(240, 158, 158)",
    "20": "rgb(240, 158, 158)",
    "21": "rgb(240, 158, 158)",
    "22": "rgb(240, 158, 158)",
    "23": "rgb(240, 158, 158)",
}

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
                            "Inpatients sorted by highest NEWS "
                            + "score in the last 12 hours"
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
        dcc.Loading(
            request_data := dcc.Store(id=f"{BPID}request_data"),
            fullscreen=True,
            type="default",
        ),
    ]
)


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])
    return html.Div(
        [
            main,
            dash_only,
        ],
    )


@callback(
    Output(request_data, "data"),
    Input(query_interval, "n_intervals"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_data(n_intervals: int):
    """
    Read data from API then store as JSON
    """
    response = requests.get(f"{get_settings().api_url}/perrt/")
    data = [PerrtWide.parse_obj(row) for row in response.json()]

    hospital_visit_ids = [perrt_entry["hospital_visit_id"] for perrt_entry in data]

    predictions_list = requests.post(
        f"{get_settings().api_url}/perrt/admission_predictions/",
        data=json.dumps(hospital_visit_ids),
    ).json()

    predictions_map = {
        p["hospital_visit_id"]: p["admission_probability"] for p in predictions_list
    }

    for entry in data:
        entry["admission_probability"] = predictions_map.get(
            str(entry["hospital_visit_id"]), 0.0
        )

    return data


@callback(
    Output(fig_perrt, "children"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def gen_simple_fig(data: list[dict]):
    # TODO: move data validation to store

    df = parse_to_data_frame(data, PerrtWide)
    df = df[["dept_name", "news_scale_1_max", "mrn"]]
    df = df.groupby(["dept_name", "news_scale_1_max"], as_index=False).count()
    df["news_scale_1_max"] = df["news_scale_1_max"].astype(int).astype(str)
    fig = px.bar(
        df,
        x="dept_name",
        y="mrn",
        color="news_scale_1_max",
        color_discrete_map=NEWS_SCORE_COLORS,
        category_orders={"news_scale_1_max": [str(x) for x in range(1, 24)]},
    )
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
