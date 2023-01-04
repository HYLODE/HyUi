"""
Layout for sub-application for the abacus endpoint
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

from web.pages.abacus import BPID, PAGE_REFRESH_INTERVAL
from web.pages.abacus.abacus import abacus_row
from web.pages.abacus.dept import (
    dropdown_dept,
    radio_icu,
    store_active_dept,
    store_dept_list,
)
from web.pages.abacus.discharges import store_discharges
from web.pages.abacus.map import (
    map_cyto_beds,
    radio_cyto_layout,
    store_elements,
    store_encounter,
    store_tapnode,
    store_selected_nodes,
)
from web.pages.abacus.node import card_node, node_debug
from web.pages.abacus.perrt import store_perrt_long, card_details
from web.pages.abacus.stores import store_beds, store_census, store_sitrep

register_page(__name__, name="ABACUS")

refresh_timer = dcc.Interval(
    id=f"{BPID}page_interval",
    interval=PAGE_REFRESH_INTERVAL,
    n_intervals=0,
)

stores = html.Div(
    [
        store_dept_list,
        store_active_dept,
        store_beds,
        store_census,
        store_sitrep,
        store_discharges,
        store_tapnode,
        store_selected_nodes,
        store_encounter,
        store_perrt_long,
        store_elements,
    ]
)

# TODO: use dbc.Tabs to create a separate view of admissions and discharges
#  for the ward in question


def layout():
    return html.Div(
        [
            # NOTE: wrapping in a separate container _seems_ to fix a problem
            # with cytoscape elements not being 'tap-able' when the
            # abacus_row was at the top of the page
            dbc.Container(
                [
                    # abacus
                    abacus_row,
                    # ward selector
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    radio_icu,
                                ]
                            ),
                            dbc.Col(
                                [
                                    dropdown_dept,
                                ]
                            ),
                            dbc.Col([radio_cyto_layout]),
                        ],
                        className="border rounded p-3 bg-light",
                    ),
                ],
                fluid=True,
            ),
            dbc.Container(
                [
                    # map and node details
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(id=f"{BPID}dept_title"),
                                    map_cyto_beds,
                                ]
                            ),
                            dbc.Col(
                                [
                                    card_node,
                                    card_details,
                                    # node_debug,
                                ],
                            ),
                        ],
                        className="border rounded p-3",
                    ),
                ],
                fluid=True,
            ),
            # placing this at the bottom else it interferes with cytoscape
            # map interactions
            html.Div(
                [
                    refresh_timer,
                    stores,
                ]
            ),
        ],
    )
