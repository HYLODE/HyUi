import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
import math
from dash import dcc, html
from pathlib import Path

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks  # noqa
from web.pages.sitrep import CAMPUSES, ids
from web.pages.sitrep.widgets import page_status_controls
from web.style import colors, replace_colors_in_stylesheet

dash.register_page(__name__, path="/sitrep/ward", name="Ward")


with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)
    cyto_style_sheet = replace_colors_in_stylesheet(cyto_style_sheet)

timers = html.Div([])
stores = html.Div(
    [
        dcc.Store(id=ids.CENSUS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE_NAMES),
    ]
)

campus_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.CAMPUS_SELECTOR,
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "UCH"][0],
            data=CAMPUSES,
        ),
    ]
)

dept_selector = html.Div(
    [
        dmc.Select(
            # label="Select a ward",
            placeholder="Select a ward",
            id=ids.DEPT_SELECTOR,
            searchable=True,
            nothingFound="No match found",
        ),
    ]
)

ward_cyto = dmc.Paper(
    [
        cyto.Cytoscape(
            id=ids.CYTO_WARD,
            style={
                # "width": "70vw",  # do not set width; will derive from height
                "height": "70vh",
                "z-index": 999,
            },
            layout={
                "name": "circle",
                "animate": True,
                "fit": True,
                "padding": 10,
                "startAngle": math.pi * 2 / 3,  # clockwise from 3 O'Clock
                "sweep": math.pi * 5 / 3,
            },
            stylesheet=cyto_style_sheet,
            responsive=True,
            userPanningEnabled=True,
            userZoomingEnabled=True,
        )
    ],
    shadow="lg",
    radius="lg",
    p="md",  # padding
    withBorder=True,
)


ward_list = dmc.Paper(
    dmc.Table(
        id=ids.BED_SELECTOR_WARD,
        striped=True,
        highlightOnHover=True,
        verticalSpacing="xxs",
        horizontalSpacing="md",
    ),
    shadow="lg",
    radius="lg",
    p="md",  # padding
    withBorder=True,
)

debug_inspector = html.Div(
    [dmc.Prism(language="json", id=ids.DEBUG_NODE_INSPECTOR_WARD, children="")]
)

bed_inspector = html.Div(
    [
        dmc.Accordion(
            children=[
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl("🛏 Bed status"),
                        dmc.AccordionPanel(id=ids.MODAL_ACCORDION_BED),
                    ],
                    value="bed_status",
                ),
                dmc.AccordionItem(
                    id=ids.MODAL_ACCORDION_PATIENT, value="patient_status"
                ),
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl("🐛 Debugging"),
                        dmc.AccordionPanel(debug_inspector),
                    ],
                    value="debug_inspector",
                ),
            ]
        )
    ]
)

inspector = html.Div(
    [
        dmc.Modal(
            id=ids.INSPECTOR_WARD,
            centered=True,
            padding="xs",
            size="60vw",
            overflow="inside",
            overlayColor=colors.gray,
            overlayOpacity=0.5,
            transition="pop",
            transitionDuration=300,
            children=[bed_inspector],
        )
    ]
)

body = dmc.Container(
    [
        page_status_controls(
            controls=[
                dmc.Col(campus_selector, span=3),
                dmc.Col(dept_selector, span="auto"),
            ],
            status=[],
        ),
        dmc.Grid(
            [
                dmc.Col(ward_cyto, span=9),
                dmc.Col(ward_list, span=3),
            ]
        ),
    ],
    style={"width": "90vw"},
    fluid=True,
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
            inspector,
        ]
    )
