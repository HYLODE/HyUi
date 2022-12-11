"""
sub-application for PERRT
"""

import dash_bootstrap_components as dbc
from datetime import datetime
import numpy as np
import pandas as pd
import warnings
from dash import Input, Output, callback
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme
from dash import html, dcc, register_page
from flask_login import current_user

# make all functions in callbacks.py available to the app
import web.pages.perrt.callbacks  # noqa: F401

from web.pages.perrt import (
    BPID,
    DEPT_COLS,
    REFRESH_INTERVAL,
    widgets,
)

register_page(__name__)

from web import icons
from web.config import get_settings
from web.convert import parse_to_data_frame, to_data_frame
from models.census import CensusRow
from models.perrt import EmapVitalsWide


register_page(__name__)


@callback(
    Output(f"{BPID}census_table", "children"),
    Input(f"{BPID}ward_data", "data"),
    prevent_initial_call=True,
)
def gen_census_table(data: dict):
    # import ipdb; ipdb.set_trace()
    dfo = pd.DataFrame.from_records(data)
    if len(dfo) == 0:
        warnings.warn("[WARN] No data provided for table")
        return html.H2("No data found for table")

    # TODO: Fix this.
    dfo["bed_label"] = dfo["bed"].str.split(pat="-", expand=True).iloc[:, 1]
    dfo["bed_label"] = dfo["bed_label"].apply(lambda x: "".join(filter(str.isdigit, x)))
    # TODO: abstract this out into a function
    dfo["room_label"] = dfo["room"]
    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("SR"), "SR", dfo["room_label"]
    )

    try:

        # https://stackoverflow.com/a/4289557/992999
        # int(''.join(filter(str.isdigit, your_string)))
        dfo["room_i"] = dfo.apply(
            lambda row: int("".join(filter(str.isdigit, row["room"]))), axis=1
        )
        dfo["room_i"] = dfo.apply(lambda row: f"Bay {row['room_i']}", axis=1)
    except ValueError:
        dfo["room_i"] = ""

    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("BY"), dfo["room_i"], dfo["room_label"]
    )
    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("CB"), "", dfo["room_label"]
    )

    # bed status icons
    dfo["bed_icons"] = ""
    llist = []
    for t in dfo.itertuples(index=False):
        closed = icons.closed(t.closed)
        covid = icons.covid(t.covid)

        icon_string = f"{closed}{covid}"
        ti = t._replace(bed_icons=icon_string)
        llist.append(ti)
    dfo = pd.DataFrame(llist, columns=dfo.columns)

    # END: Prepare icons
    # --------------------

    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    dfo.sort_values(by=["department", "room", "bed"], inplace=True)

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=[
                {"id": "bed_icons", "name": "", "presentation": "markdown"},
                {"id": "bed_label", "name": "Bed", "type": "text"},
                {"id": "room_label", "name": ""},
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
                {
                    "if": {
                        "filter_query": "{closed} contains true",
                        # "column_id": "closed"
                    },
                    "color": "maroon",
                },
            ],
            # sort_action="native",
            markdown_options={"html": True},
            persistence=True,
            persisted_props=["data"],
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

dept_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Ward details")),
        dbc.CardBody(id=f"{BPID}dept_table"),
    ]
)

census_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("census details")),
        dbc.CardBody(id=f"{BPID}census_table"),
    ]
)

config_footer = dbc.Card(
    [
        dbc.CardHeader(html.H6("Settings")),
        dbc.CardBody(id=f"{BPID}settings", children=[widgets.closed_beds_switch]),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Loading(
            [
                dcc.Store(id=f"{BPID}dept_data"),
                dcc.Store(id=f"{BPID}beds_data"),
                dcc.Store(id=f"{BPID}census_data"),
            ],
            fullscreen=True,
            type="default",
        ),
        dcc.Store(id=f"{BPID}patients_data"),
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
            dbc.Row(
                [
                    dbc.Col(
                        [config_footer],
                    ),
                ]
            ),
            dash_only,
        ]
    )
