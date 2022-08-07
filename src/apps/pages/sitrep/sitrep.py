# src/apps/sitrep/sitrep.py
"""
sub-application for sitrep
"""


import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import warnings
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import dcc, html, register_page


from apps.pages.sitrep import (
    BPID,
    STYLE_CELL_CONDITIONAL,
    widgets,
    COLS,
    REFRESH_INTERVAL,
)
from apps.pages.sitrep.callbacks import (
    store_beds,
    store_ward,
    store_census,
    store_patients,
    store_sitrep,
    store_hymind_icu_discharge,
    diff_table,
)
from config.settings import settings
from utils import icons

register_page(__name__)


@callback(
    Output(f"{BPID}fancy_table", "children"),
    Input(f"{BPID}ward_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    dfo = pd.DataFrame.from_records(data)
    if len(dfo) == 0:
        warnings.warn("[WARN] No data provided for table")
        return html.H2("No data found for table")
    if settings.VERBOSE and len(dfo):
        print(dfo.iloc[0])

    # import ipdb; ipdb.set_trace()
    dfo["bed_label"] = dfo["bed"].str.split(pat="-", expand=True).iloc[:, 1]
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

    dfo["age_sex"] = dfo.apply(
        lambda row: f"{row['age']:.0f}{row['sex']} " if row["mrn"] else "",
        axis=1,
    )
    # TODO: format this in dash so can change colour with number
    # import ipdb; ipdb.set_trace()
    dfo["prediction_as_real"] = dfo["prediction_as_real"].apply(
        lambda x: f"{100*x:0.0f}%" if not pd.isna(x) else ""
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
    dfo = pd.DataFrame(llist, columns=dfo.columns)

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

    # dfn["open"] = dfn["closed"].apply(icons.closed)
    # dfn["covid"] = dfn["covid"].apply(icons.covid)
    # END: Prepare icons
    # --------------------

    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    dfo.sort_values(by="unit_order", inplace=True)

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=COLS,
            data=dfo.to_dict("records"),
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
        dcc.Store(id=f"{BPID}hymind_icu_discharge_data"),
        dcc.Store(id=f"{BPID}patients_data"),
        dcc.Store(id=f"{BPID}ward_data"),
    ]
)

layout = html.Div(
    [
        dbc.Row(dbc.Col([widgets.ward_radio_button])),
        dbc.Row(dbc.Col([sitrep_table])),
        dash_only,
    ]
)
