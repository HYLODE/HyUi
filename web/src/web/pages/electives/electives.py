import dash_bootstrap_components as dbc
import plotly.express as px
import requests
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html, register_page
from flask_login import current_user

from models.electives import MergedData, SurgData  # ElectiveSurgCase,
from web.config import get_settings
from web.convert import parse_to_data_frame
from web.pages.electives import (
    BPID,
    SPECIALTY_SHORTNAMES,
    STYLE_CELL_CONDITIONAL,
)

register_page(__name__)

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
                        value=[],
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
    Input(days_ahead_slider, "value"),
)
def store_data(days_ahead: int):
    response = requests.get(
        f"{get_settings().api_url}/electives/", params={"days_ahead": days_ahead}
    )
    return [MergedData.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(filtered_data, "data"),
    Input(service_picker, "value"),
    Input(pacu_checklist, "value"),
    Input(request_data, "data"),
)
def filter_data(service: list[str], pacu: list[bool], data: list[dict]):
    """
    Update data based on picker
    """

    # TODO: Fix this.
    # data = [row for row in data if row["pacu"] in pacu]
    if service:
        return [row for row in data if row["PrimaryService"] in service]
    return data


@callback(
    Output(fig_electives, "children"),
    Input(filtered_data, "data"),
    prevent_initial_call=True,
)
def gen_surgeries_over_time(data: list[dict]):
    """
    Plot stacked bar
    """
    if not data:
        return html.H2("No data to plot")

    df = parse_to_data_frame(data, SurgData)
    df = (
        df.groupby("PrimaryService")
        .resample("24H", on="PlannedOperationStartInstant")
        .agg({"PatientDurableKey": "size"})
    )
    df.reset_index(inplace=True)
    fig = px.bar(
        df,
        x="PlannedOperationStartInstant",
        y="PatientDurableKey",
        color="pacu",
    )
    return dcc.Graph(id=f"{BPID}fig", figure=fig)


@callback(
    Output(table_electives, "children"),
    Input(filtered_data, "data"),
)
def gen_table_consults(data: list[dict]):
    if not data:
        return html.H2("No data to tabulate")

    dfo = parse_to_data_frame(data, MergedData)

    # dfo["pacu"] = dfo["pacu"].apply(lambda x: "PACU" if x else "")
    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['AgeInYears']:.0f}{row['Sex'][:1]} ",
        axis=1,
    )

    def _display_name(row):
        FirstName = row["FirstName"].title()
        LastName = row["LastName"].upper()
        return f"{FirstName} {LastName}"

    dfo["name"] = dfo.apply(_display_name, axis="columns")

    dfo["RoomName"] = dfo["RoomName"].fillna("")
    dfo["RoomName"] = dfo["RoomName"].apply(
        lambda x: "" if "Not Applicable" in x else x
    )
    dfo["PrimaryService"] = dfo["PrimaryService"].fillna("")
    dfo["PrimaryService"] = dfo["PrimaryService"].apply(
        lambda x: x.replace("Surgery", "" if x else "")
    )
    dfo["PrimaryService"] = dfo["PrimaryService"].apply(
        lambda x: SPECIALTY_SHORTNAMES.get(x, x)
    )
    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    dfo.sort_values(by="SurgeryDate", ascending=True, inplace=True)

    return [
        dt.DataTable(
            id=f"{BPID}_data_table",
            columns=[
                # {"id": "SurgeryDate", "name": "Date"},
                {"id": "pacu", "name": "pacu"},
                # {"id": "PrimaryService", "name": "Specialty"},
                # {"id": "RoomName", "name": "Theatre"},
                {"id": "age_sex", "name": ""},
                {"id": "name", "name": "Full Name"},
                {"id": "PrimaryMrn", "name": "MRN"},
                #   {"id": "PatientFriendlyName", "name": "Procedure"},
                {"id": "preassess_date", "name": "Pre-assess Date"},
                {"id": "asa", "name": "asa"},
                {"id": "c_line", "name": "Central line consent"},
                {"id": "resp", "name": "resp condition count"},
                {"id": "cardio", "name": "cardio"},
                {"id": "haem", "name": "haem"},
                {"id": "anaesthetic_alert", "name": "anaesthetic_alert"},
                {"id": "CRP_abnormal_count", "name": "CRP_abnormal_count"},
                {"id": "INR_last_value", "name": "INR_last_value"},
                {"id": "NA_max_value", "name": "NA_max_value"},
                {"id": "PatientDurableKey", "name": "key"},
                {"id": "EchoPerformed", "name": "EchoPerformed"},
                {"id": "EchoAbnormal", "name": "EchoAbnormal"},
                {"id": "SYS_BP_abnormal_count", "name": "SYS_BP_abnormal_count"},
                {"id": "DIAS_BP_abnormal_count", "name": "DIAS_BP_abnormal_count"},
                {"id": "PULSE_measured_count", "name": "PULSE_measured_count"},
                {"id": "BMI_max_value", "name": "BMI"},
                {"id": "simple_score", "name": "simple_score"},
            ],
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
def update_service_dropdown(data: list[dict]):

    df = parse_to_data_frame(data, MergedData)
    return df["PrimaryService"].sort_values().unique()
