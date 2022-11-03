"""
sub-application for electives
"""

from typing import List

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from dash import Input, Output, State, callback, get_app
from dash import dash_table as dt
from dash import dcc, html, register_page
from flask_caching import Cache
from flask_login import current_user

from models.electives import GetElectiveRow
from web.config import get_settings
from web.convert import parse_to_data_frame
from web.pages.electives import (
    BPID,
    COLS,
    REFRESH_INTERVAL,
    SPECIALTY_SHORTNAMES,
    STYLE_CELL_CONDITIONAL,
)

CACHE_TIMEOUT = 4 * 3600

register_page(__name__)
app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)

card_fig = dbc.Card(
    [
        dbc.CardHeader(html.H6("Elective Surgery over the next week")),
        dbc.CardBody(
            [
                html.Div(
                    [
                        dbc.Label("PACU"),
                        pacu_checklist := dbc.Checklist(
                            options=[
                                {"label": "Booked", "value": True},
                                {"label": "Not booked", "value": False},
                            ],
                            value=[True],
                            inline=True,
                        ),
                    ]
                ),
                html.Div(
                    service_picker := dcc.Dropdown(
                        value="",
                        placeholder="Pick a surgical specialty",
                        multi=True,
                    )
                ),
                html.Div(
                    [
                        html.P(
                            (
                                "Pick a range of days over the next "
                                "week (data refreshes every night)"
                            )
                        )
                    ]
                ),
                html.Div(
                    days_ahead_slider := dcc.Slider(min=2, max=7, step=1, value=4)
                ),
                fig_electives := html.Div(),
            ]
        ),
    ]
)

card_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Elective surgery")),
        dbc.CardBody(
            [
                table_electives := html.Div(),
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
        filtered_data := dcc.Store(id=f"{BPID}filtered_data"),
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
    Input(days_ahead_slider, "value"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_data(n_intervals: int, days_ahead: int):
    """
    Read data from API then store as JSON
    """
    # data = get_results_response(API_URL, params={"days_ahead": days_ahead})
    response = requests.get(
        f"{get_settings().api_url}/electives", params={"days_ahead": days_ahead}
    )
    return [GetElectiveRow.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(filtered_data, "data"),
    Input(service_picker, "value"),
    Input(pacu_checklist, "value"),
    Input(request_data, "data"),
    prevent_initial_call=True,  # Can probably remove as this function is called anyway.
)
def filter_data(service: List[str], pacu: List[bool], data: list):
    """
    Update data based on picker
    """

    # Dash seems to send a list with an empty dict if there is no data.
    # TODO: Figure out why an empty dict is arriving here.
    if len(data) == 1 and not data[0]:
        return {}

    data = [row for row in data if row["pacu"] in pacu]  # type: ignore
    if service:
        data = [row for row in data if row["SurgicalService"] in service]
    return data


@callback(
    Output(fig_electives, "children"),
    Input(filtered_data, "modified_timestamp"),
    State(filtered_data, "data"),
    prevent_initial_call=True,
)
def gen_surgeries_over_time(n_intervals: int, data: list[dict]):
    """
    Plot stacked bar
    """
    if len(data) == 0:
        return html.H2("No data to plot")
    df = parse_to_data_frame(data, GetElectiveRow)
    df = (
        df.groupby("SurgicalService")
        .resample("24H", on="PlannedOperationStartInstant")
        .agg({"PatientKey": "size"})
    )
    df.reset_index(inplace=True)
    # print(df)
    fig = px.bar(
        df, x="PlannedOperationStartInstant", y="PatientKey", color="SurgicalService"
    )
    return dcc.Graph(id=f"{BPID}fig", figure=fig)


@callback(
    Output(table_electives, "children"),
    Input(filtered_data, "modified_timestamp"),
    State(filtered_data, "data"),
    prevent_initial_call=True,
)
def gen_table_consults(modified: int, data: dict):
    if len(data) == 0:
        return html.H2("No data to tabulate")
    dfo = pd.DataFrame.from_records(data)
    dfo["pacu"] = dfo["pacu"].apply(lambda x: "PACU" if x else "")
    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['AgeInYears']:.0f}{row['Sex'][:1]} ",
        axis=1,
    )

    dfo["name"] = dfo.apply(
        lambda row: f"{row.FirstName.title()} {row.LastName.upper()}", axis=1
    )
    dfo["RoomName"] = dfo["RoomName"].fillna("")
    dfo["RoomName"] = dfo["RoomName"].apply(
        lambda x: "" if "Not Applicable" in x else x
    )
    dfo["SurgicalService"] = dfo["SurgicalService"].fillna("")
    dfo["SurgicalService"] = dfo["SurgicalService"].apply(
        lambda x: x.replace("Surgery", "" if x else "")
    )
    dfo["SurgicalService"] = dfo["SurgicalService"].apply(
        lambda x: SPECIALTY_SHORTNAMES.get(x, x)
    )
    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    dfo.sort_values(by="SurgeryDate", ascending=True, inplace=True)

    return [
        dt.DataTable(
            id=f"{BPID}_data_table",
            columns=COLS,
            data=dfo.to_dict("records"),
            style_table={"width": "100%", "minWidth": "100%", "maxWidth": "100%"},
            style_as_list_view=True,  # remove col lines
            style_cell={
                "fontSize": 13,
                "font-family": "monospace",
                "padding": "1px",
                "textAlign": "left",
            },
            style_cell_conditional=STYLE_CELL_CONDITIONAL,
            style_data={"color": "black", "backgroundColor": "white"},
            # striped rows
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(220, 220, 220)",
                },
                {
                    "if": {
                        "filter_query": "{pacu} contains 'PACU'",
                        # "column_id": "closed"
                    },
                    "color": "maroon",
                },
            ],
            filter_action="native",
            sort_action="native",
        )
    ]


@callback(
    Output(service_picker, "options"),
    Input(request_data, "data"),
    prevent_initial_call=True,
)
def update_service_dropdown(data: list):

    # TODO: Figure out why an empty dict is arriving here.
    if len(data) == 1 and not data[0]:
        return []

    df = parse_to_data_frame(data, GetElectiveRow)
    return df["surgical_service"].sort_values().unique()
