"""
sub-application for PERRT
"""

import warnings

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dash_table as dt, dcc, html, register_page
from dash.dash_table.Format import Format, Scheme
from flask_login import current_user

# makes all functions in callbacks.py available to the app
import web.pages.perrt.callbacks  # noqa: F401
from web.pages.perrt import (
    BPID,
    REFRESH_INTERVAL,
    widgets,
)

register_page(__name__)


@callback(
    Output(f"{BPID}census_table", "children"),
    Input(f"{BPID}census_data", "data"),
    prevent_initial_call=True,
)
def gen_census_table(data: dict):
    """
    Prepare a table of patients
    :param data: census data
    :return:
    """
    dfo = pd.DataFrame.from_records(data)
    if len(dfo) == 0:
        warnings.warn("[WARN] No data provided for table")
        return html.H2("No data found for table")

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=[
                # {"id": "bed_icons", "name": "", "presentation": "markdown"},
                # {"id": "room_label", "name": ""},
                {"id": "bed_label", "name": "Bed", "type": "text"},
                # {"id": "age_sex", "name": ""},
                {
                    "id": "age",
                    "name": "age",
                    "type": "numeric",
                    "format": Format(precision=0, scheme=Scheme.fixed),
                },
                {"id": "sex", "name": "sex"},
                {"id": "name", "name": "Full Name"},
                {"id": "mrn", "name": "MRN", "type": "text"},
                {"id": "encounter", "name": "CSN", "type": "text"},
                {
                    "id": "los",
                    "name": "LoS",
                    "type": "numeric",
                    "format": Format(precision=0, scheme=Scheme.fixed),
                },
                {"id": "name_cpr", "name": "CPR", "type": "text"},
                # {
                #     "id": "status_change_datetime",
                #     "name": "CPR timestamp",
                #     "type": "datetime",
                # },
                # {"id": "name_consults", "name": "Consult", "type": "text"},
                {
                    "id": "status_change_datetime_consults",
                    "name": "Last PERRT",
                    "type": "datetime",
                },
                {
                    "id": "news_max",
                    "name": "NEWS",
                    "type": "numeric",
                    "format": Format(precision=0, scheme=Scheme.fixed),
                },
            ],
            data=dfo.to_dict("records"),
            editable=True,
            # fixed_columns={},
            style_table={"width": "100%", "minWidth": "100%", "maxWidth": "100%"},
            style_as_list_view=True,  # remove col lines
            style_cell={
                "fontSize": 13,
                "font-family": "monospace",
                "padding": "1px",
            },
            # style_cell_conditional=CENSUS_STYLE_CELL_CONDITIONAL,
            style_data={"color": "black", "backgroundColor": "white"},
            # striped rows
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(220, 220, 220)",
                },
            ],
            markdown_options={"html": True},
            persistence=True,
            persisted_props=["data"],
            filter_action="native",
            sort_action="native",
        ),
    )

    # wrap in container
    return (
        dbc.Container(
            dto,
            className="dbc",
        ),
    )


dept_selector = dbc.Card(
    [
        dbc.CardHeader(html.H6("Select a ward")),
        dbc.CardBody(html.Div(id=f"{BPID}dept_dropdown_div")),
    ]
)

census_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("census details")),
        dbc.CardBody(id=f"{BPID}census_table"),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}dept_data"),
        dcc.Store(id=f"{BPID}census_data"),
        dcc.Store(id=f"{BPID}ward_data"),
        # Need a hidden div for the callback with no output
        html.Div(id="hidden-div-diff-table", style={"display": "none"}),
    ]
)


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [widgets.building_radio_button],
                        width={"size": 6, "order": "last", "offset": 6},
                    ),
                ]
            ),
            # dbc.Row(dbc.Col([dept_table])),
            dbc.Row(dbc.Col([dept_selector])),
            dbc.Row(dbc.Col([census_table])),
            dash_only,
        ]
    )
