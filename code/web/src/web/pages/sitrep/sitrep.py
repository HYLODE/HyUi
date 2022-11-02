import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, callback
from dash import dash_table as dt
from dash import html, dcc, register_page
from flask_login import current_user

from web.pages.sitrep import (
    BPID,
    STYLE_CELL_CONDITIONAL,
    widgets,
    COLS,
    REFRESH_INTERVAL,
    PROBABILITY_COLOUR_SCALE,
)

import web.pages.sitrep.callbacks  # noqa

from utils import icons

register_page(__name__)


@callback(
    Output(f"{BPID}fancy_table", "children"),
    Input(f"{BPID}ward_data", "data"),
    # prevent_initial_call=True,
)
def gen_fancy_table(data: dict):
    df = pd.DataFrame.from_records(data)

    df["bed_label"] = df["bed"].str.split(pat="-", expand=True).iloc[:, 1]
    df["bed_label"] = df["bed_label"].apply(lambda x: "".join(filter(str.isdigit, x)))
    # TODO: abstract this out into a function
    df["room_label"] = df["room"]
    df["room_label"] = np.where(
        df["room"].astype(str).str.contains("SR"), "SR", df["room_label"]
    )
    df["bed_functional"] = df["bed_functional"].apply(lambda row: "|".join(row))
    df["bed_physical"] = df["bed_physical"].apply(lambda row: "|".join(row))

    # predicts bed to still be occupied so invert
    # 2022-10-11 reverting back
    # df["prediction_as_real"] = 1 - df["prediction_as_real"]

    try:

        # https://stackoverflow.com/a/4289557/992999
        # int(''.join(filter(str.isdigit, your_string)))
        df["room_i"] = df.apply(
            lambda row: int("".join(filter(str.isdigit, row["room"]))), axis=1
        )
        df["room_i"] = df.apply(lambda row: f"Bay {row['room_i']}", axis=1)
    except ValueError:
        df["room_i"] = ""

    df["room_label"] = np.where(
        df["room"].astype(str).str.contains("BY"), df["room_i"], df["room_label"]
    )
    df["room_label"] = np.where(
        df["room"].astype(str).str.contains("CB"), "", df["room_label"]
    )

    df["age_sex"] = df.apply(
        lambda row: f"{row['age']:.0f}{row['sex']} " if row["mrn"] else "",
        axis=1,
    )
    # TODO: format this in dash so can change colour with number
    # import ipdb; ipdb.set_trace()
    # df["prediction_as_real"] = df["prediction_as_real"].apply(
    #     lambda x: f"{100*x:0.0f}%" if not pd.isna(x) else ""
    # )

    # --------------------
    # START: Prepare icons
    # organ support icons
    df["organ_icons"] = ""
    llist = []
    for t in df.itertuples(index=False):

        cvs = icons.cvs(t.n_inotropes_1_4h)
        rs = icons.rs(t.vent_type_1_4h)
        aki = icons.aki(t.had_rrt_1_4h)

        icon_string = f"{rs}{cvs}{aki}"
        ti = t._replace(organ_icons=icon_string)
        llist.append(ti)
    df = pd.DataFrame(llist, columns=df.columns)

    # bed status icons
    df["bed_icons"] = ""
    llist = []
    for t in df.itertuples(index=False):

        closed = icons.closed(t.closed)
        covid = icons.covid(t.covid)

        icon_string = f"{closed}{covid}"
        ti = t._replace(bed_icons=icon_string)
        llist.append(ti)
    df = pd.DataFrame(llist, columns=df.columns)

    # dfn["open"] = dfn["closed"].apply(icons.closed)
    # dfn["covid"] = dfn["covid"].apply(icons.covid)
    # END: Prepare icons
    # --------------------

    # Sort into unit order / displayed tables will NOT be sortable
    # ------------------------------------------------------------
    df.sort_values(by="unit_order", inplace=True)

    dto = (
        dt.DataTable(
            id=f"{BPID}tbl-census",
            columns=COLS,
            data=df.to_dict("records"),
            editable=True,
            # fixed_columns={},
            style_table={"width": "100%", "minWidth": "100%", "maxWidth": "100%"},
            dropdown={
                "DischargeReady": {
                    "options": [
                        {"label": "READY", "value": "ready"},
                        {"label": "Review", "value": "review"},
                        {"label": "-", "value": "No"},
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
                # {
                #     "if": {"row_index": "odd"},
                #     "backgroundColor": "rgb(220, 220, 220)",
                # },
                {
                    "if": {
                        "filter_query": "{closed} contains true",
                        # "column_id": "closed"
                    },
                    "color": "maroon",
                },
                *PROBABILITY_COLOUR_SCALE,
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
    return (
        dbc.Container(
            dto,
            className="dbc",
        ),
    )


sitrep_table = dbc.Card(
    [
        dbc.CardHeader(html.H6("Sitrep details")),
        dbc.CardBody(id=f"{BPID}fancy_table"),
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
        dcc.Store(id=f"{BPID}beds_data"),
        dcc.Loading(
            [
                dcc.Store(id=f"{BPID}ward_data"),
            ],
            fullscreen=True,
            type="default",
        ),
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
                        [widgets.ward_radio_button],
                        width={"size": 6, "order": "last", "offset": 6},
                    ),
                ]
            ),
            dbc.Row(dbc.Col([sitrep_table])),
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
