import dash
import dash_mantine_components as dmc
import json
import warnings
from dash import dash_table as dtable, html
from pathlib import Path
from datetime import date, timedelta


import web.pages.electives.callbacks  # noqa
from web.pages.electives import CAMPUSES, ids
from web.style import replace_colors_in_stylesheet

warnings.warn("\nINFO: Confirm that you have imported all the callbacks")

dash.register_page(__name__, path="/surgery/electives", name="Electives")

with open(Path(__file__).parent / "table_style_sheet.json") as f:
    table_style_sheet = json.load(f)
    table_style_sheet = replace_colors_in_stylesheet(table_style_sheet)

timers = html.Div([])
stores = html.Div(
    [
        # dcc.Store(id=ids.CENSUS_STORE),
    ]
)
notifications = html.Div(
    [
        # html.Div(id=ids.ACC_BED_SUBMIT_WARD_NOTIFY),
    ]
)

campus_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.CAMPUS_SELECTOR,
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "UCH"][0],
            data=CAMPUSES,
            persistence=True,
            persistence_type="local",
        ),
    ]
)


electives_list = dmc.Paper(
    dtable.DataTable(
        id=ids.ELECTIVES_TABLE,
        columns=[
            {"id": "pacu", "name": "PACU"},
            {"id": "room_name", "name": "Room"},
            {"id": "primary_service", "name": "Specialty"},
            {"id": "patient_friendly_name", "name": "Operation"},
            {"id": "primary_mrn", "name": "MRN"},
            {"id": "first_name", "name": "First Name"},
            {"id": "last_name", "name": "Last Name"},
            {"id": "age_in_years", "name": "Age"},
            {"id": "sex", "name": "Sex"},
            #            {"id": "abnormal_echo", "name": "abnormal_echo"},
            # {
            #     "id": "icu_prob",
            #     "name": "prediction",
            #     "type": "numeric",
            #     "format": {"specifier": ".1f"},
            # },
        ],
        data=[],
        # style_table={"width": "50%", "minWidth": "50%", "maxWidth": "100%"},
        style_as_list_view=True,  # remove col lines
        style_cell={
            "fontSize": 11,
            "padding": "5px",
        },
        style_cell_conditional=table_style_sheet,
        style_data={"color": "black", "backgroundColor": "white"},
        # striped rows
        markdown_options={"html": True},
        persistence=True,
        persisted_props=["data"],
        sort_action="native",
        filter_action="native",
    ),
    shadow="lg",
    p="md",  # padding
    withBorder=True,
)

debug_inspector = dmc.Container(
    [
        dmc.Spoiler(
            children=[
                dmc.Prism(
                    language="json",
                    # id=ids.DEBUG_NODE_INSPECTOR_WARD, children=""
                )
            ],
            showLabel="Show more",
            hideLabel="Hide",
            maxHeight=100,
        )
    ]
)

inspector = html.Div(
    [
        # dmc.Modal(
        #     id=ids.INSPECTOR_WARD_MODAL,
        #     centered=True,
        #     padding="xs",
        #     size="60vw",
        #     overflow="inside",
        #     overlayColor=colors.gray,
        #     overlayOpacity=0.5,
        #     transition="fade",
        #     transitionDuration=0,
        #     children=[bed_inspector],
        # )
    ]
)

body = dmc.Container(
    dmc.Grid(
        [
            dmc.Col(campus_selector, offset=9, span=3),
            dmc.Tabs(
                [
                    dmc.TabsList(
                        [
                            dmc.Tab(
                                date.today().strftime("%A %B %d"),
                                value=date.today(),
                            ),
                            dmc.Tab(
                                (date.today() + timedelta(days=1)).strftime("%A %B %d"),
                                value=(date.today() + timedelta(days=1)),
                            ),
                            dmc.Tab(
                                (date.today() + timedelta(days=2)).strftime("%A %B %d"),
                                value=(date.today() + timedelta(days=2)),
                            ),
                        ],
                        id="date_selected",
                        grow=True,
                    ),
                    dmc.TabsPanel(electives_list, value=date.today()),
                    dmc.TabsPanel(
                        electives_list, value=(date.today() + timedelta(days=1))
                    ),
                    dmc.TabsPanel(
                        electives_list, value=(date.today() + timedelta(days=2))
                    ),
                ],
                orientation="horizontal",
                value=date.today(),
            ),
        ]
    ),
    style={"width": "100vw"},
    fluid=True,
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            notifications,
            body,
            inspector,
        ]
    )
