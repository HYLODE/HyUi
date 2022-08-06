# src/apps/sitrep/sitrep.py
"""
sub-application for sitrep
"""

from collections import OrderedDict

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import requests
from dash import Input, Output, State, callback
from dash import dash_table as dt
from dash import dcc, html, register_page

import utils
from apps.pages.sitrep import BPID, STYLE_CELL_CONDITIONAL, widgets
from apps.pages.sitrep.callbacks import *
from config.settings import settings
from utils import icons
from utils.beds import BedBonesBase, get_bed_list, unpack_nested_dict, update_bed_row
from utils.dash import df_from_store, get_results_response, validate_json

register_page(__name__)


@callback(
    Output(f"{BPID}fancy_table", "children"),
    Input(f"{BPID}wrangled_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    dfo = pd.DataFrame.from_records(data)
    if settings.VERBOSE:
        print(dfo.iloc[0])

    # import ipdb; ipdb.set_trace()
    dfo["bed_label"] = dfo["bed"].str.split(pat="-", expand=True).iloc[:, 1]
    dfo["room_label"] = dfo["room"]
    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("SR"), "SR", dfo["room_label"]
    )

    dfo["room_i"] = dfo.apply(lambda row: f"Bay {int(row['room'][2:])}", axis=1)
    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("BY"), dfo["room_i"], dfo["room_label"]
    )
    dfo["room_label"] = np.where(
        dfo["room"].astype(str).str.contains("CB"), "", dfo["room_label"]
    )

    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['age']:.0f}{row['sex']} " if row["mrn"] else "",
        axis=1,
    )

    # --------------------
    # START: Prepare icons
    # organ support icons
    dfo["organ_icons"] = ""
    llist = []
    for t in dfo.itertuples(index=False):

        cvs = icons.cvs(t.n_inotropes_1_4h)
        rs = icons.rs(t.vent_type_1_4h)
        aki = icons.aki(t.had_rrt_1_4h)

        icon_string = f"{rs}{cvs}{aki}"
        ti = t._replace(organ_icons=icon_string)
        llist.append(ti)
    dfn = pd.DataFrame(llist, columns=dfo.columns)

    # bed status icons
    dfn["open"] = dfn["closed"].apply(icons.closed)
    # END: Prepare icons
    # --------------------

    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    dfn.sort_values(by="unit_order", inplace=True)

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=COLS,
            data=dfn.to_dict("records"),
            editable=True,
            # fixed_columns={},
            style_table={"width": "100%", "minWidth": "100%", "maxWidth": "100%"},
            dropdown={
                "DischargeReady": {
                    "options": [
                        {"label": "READY", "value": "ready"},
                        {"label": "Review", "value": "review"},
                        {"label": "No", "value": "No"},
                    ],
                    "clearable": False,
                },
            },
            style_as_list_view=True,  # remove col lines
            style_cell={
                "fontSize": 13,
                "font-family": "monospace",
                "padding": "1px",
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
                        "filter_query": "{closed} contains true",
                        # "column_id": "closed"
                    },
                    "color": "maroon",
                },
            ],
            # sort_action="native",
            # sort_by=[
            #     {"column_id": "unit_order", "direction": "asc"},
            # ],
            # cell_selectable=True,  # possible to click and navigate cells
            # row_selectable="single",
            markdown_options={"html": True},
            persistence=True,
            persisted_props=["data"],
        ),
    )

    # wrap in container
    dto = [
        dbc.Container(
            dto,
            className="dbc",
        )
    ]
    return dto


sitrep_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Sitrep details")),
        dbc.CardBody(id=f"{BPID}fancy_table"),
    ]
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query-interval", interval=REFRESH_INTERVAL, n_intervals=0
        ),
        dcc.Store(id=f"{BPID}beds_data"),
        dcc.Store(id=f"{BPID}census_data"),
        dcc.Store(id=f"{BPID}sitrep_data"),
        dcc.Store(id=f"{BPID}wrangled_data"),
        dcc.Store(id=f"{BPID}hymind_icu_discharge_data"),
    ]
)

layout = html.Div(
    [
        dbc.Row(dbc.Col([widgets.ward_radio_button])),
        dbc.Row(dbc.Col([sitrep_table])),
        dash_only,
    ]
)
