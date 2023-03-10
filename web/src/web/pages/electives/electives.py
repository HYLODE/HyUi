import dash
import dash_mantine_components as dmc
import json
from dash import dash_table as dtable, html
from pathlib import Path
from datetime import date, timedelta

import web.pages.electives.callbacks  # noqa
from web.pages.electives import CAMPUSES, ids
from web.style import replace_colors_in_stylesheet


import logging

logger = logging.getLogger(__name__)
logger.debug("Confirm that you have imported all the callbacks")

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
pacu_selector = html.Div(
    [
        dmc.SegmentedControl(
            id="pacu_selector",
            value="",
            data=[
                {
                    "value": "",
                    "label": "All",
                },
                {
                    "value": "BOOKED",
                    "label": "PACU",
                },
                {
                    "value": "No",
                    "label": "Not PACU",
                },
            ],
            persistence=True,
            persistence_type="local",
        ),
    ]
)

date_selector = html.Div(
    # dmc.Tooltip(
    #     label="Double-click on a date to select a single day",
    #     multiline=True,
    #     position="top",
    #     openDelay=500,
    #     children=[
    dmc.DateRangePicker(
        id="date_selector",
        minDate=date.today(),
        maxDate=date.today() + timedelta(days=10),
        allowSingleDateInRange=True,
        fullWidth=True,
        value=[date.today(), (date.today() + timedelta(days=3))],
    ),
    # ],
    # )
)


electives_list = dmc.Paper(
    dtable.DataTable(
        id=ids.ELECTIVES_TABLE,
        columns=[
            {"id": "surgery_date", "name": "Date"},
            {"id": "pacu_yn", "name": "PACU"},
            {"id": "preassess_status", "name": "Preassessment"},
            {"id": "full_name", "name": "Full Name"},
            {"id": "age_sex", "name": "Age / Sex"},
            {"id": "patient_friendly_name", "name": "Operation"},
            {"id": "primary_mrn", "name": "MRN"},
            {"id": "room_name", "name": "Theatre"},
            #            {"id": "abnormal_echo", "name": "abnormal_echo"},
            # {
            #     "id": "icu_prob",
            #     "name": "prediction",
            #     "type": "numeric",
            #     "format": {"specifier": ".1f"},
            # },
        ],
        # data=[],
        style_table={"overflowX": "scroll"},
        style_as_list_view=True,  # remove col lines
        style_cell={
            "fontSize": 11,
            "padding": "5px",
        },
        style_cell_conditional=table_style_sheet,
        style_data={"color": "black", "backgroundColor": "white"},
        # striped rows
        markdown_options={"html": True},
        persistence=False,
        persisted_props=["data"],
        sort_action="native",
        filter_action="native",
        filter_query="",
    ),
    shadow="lg",
    p="md",  # padding
    withBorder=True,
)

patient_info_box = dmc.Paper(dmc.Code(id="patient_info_box", block=True))

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
    [
        dmc.Grid(
            children=[
                dmc.Col(pacu_selector, span=4),
                dmc.Col(campus_selector, span=3),
                dmc.Col(date_selector, span=5),
                dmc.Col(electives_list, span=7),
                dmc.Col(patient_info_box, span=5),
            ],
        ),
    ],
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
