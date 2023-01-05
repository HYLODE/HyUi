"""
Layout for sub-application for the abacus endpoint
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page
from flask_login import current_user  # noqa

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
    store_selected_nodes,
    store_tapnode,
)
from web.pages.abacus.node import card_node, debug_toggle, node_debug
from web.pages.abacus.perrt import card_details, store_perrt_long
from web.pages.abacus.stores import store_beds, store_census, store_sitrep
from web.pages.login import not_logged_in_div_content

register_page(__name__, name="SITREP")

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

not_logged_in_container = html.Div([not_logged_in_div_content])


def layout():
    if not current_user.is_authenticated:
        return not_logged_in_container

    # TODO: use dbc.Tabs to create a separate view of admissions and discharges
    #  for the ward in question
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
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dropdown_dept,
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    radio_cyto_layout,
                                ],
                                width=5,
                            ),
                            dbc.Col(
                                [
                                    debug_toggle,
                                ],
                                width=1,
                            ),
                        ],
                        justify="between",
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
                                    dbc.Fade(
                                        node_debug,
                                        id=f"{BPID}node_debug_fade",
                                        is_in=False,
                                        appear=False,
                                    ),
                                ],
                            ),
                        ],
                        className="border rounded p-3",
                    ),
                ],
                fluid=True,
            ),
            html.Div(
                [
                    refresh_timer,
                    stores,
                ]
            ),
        ],
    )
