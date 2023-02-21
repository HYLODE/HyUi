import dash
from dash import dcc
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
from dash import dcc, html
from pathlib import Path

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.perrt.callbacks.cytoscape  # noqa
import web.pages.perrt.callbacks.inspector  # noqa
import web.pages.perrt.callbacks.widgets  # noqa
from web.pages.perrt import CAMPUSES, ids
from web.style import colors, replace_colors_in_stylesheet

dash.register_page(__name__, path="/sitrep/perrt", name="PERRT")

with open(Path(__file__).parent / "cyto_style_sheet.json") as f:
    cyto_style_sheet = json.load(f)
    cyto_style_sheet = replace_colors_in_stylesheet(cyto_style_sheet)

timers = html.Div([])
stores = html.Div(
    [
        dcc.Loading(dcc.Store(id=ids.CENSUS_STORE), fullscreen=True, type="dot"),
        dcc.Loading(dcc.Store(id=ids.NEWS_STORE), fullscreen=True, type="dot"),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE_NAMES),
        dcc.Store(id=ids.ACC_BED_SUBMIT_STORE),
    ]
)

notifications = html.Div(
    [
        html.Div(id=ids.ACC_BED_SUBMIT_CAMPUS_NOTIFY),
    ]
)

campus_selector = dmc.Container(
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

dept_selector = dmc.Container(
    [
        dmc.Select(
            label="Select a ward",
            placeholder="ward",
            id=ids.DEPT_SELECTOR,
        ),
    ]
)

campus_status = dmc.Paper(
    [
        dmc.Progress(
            id=ids.PROGRESS_CAMPUS,
            size=20,
            radius="md",
            # style={"font-size": "10px", "font-weight": 300},
        )
    ],
)

campus_cyto = dmc.Paper(
    [
        cyto.Cytoscape(
            id=ids.CYTO_CAMPUS,
            style={
                # "width": "70vw",
                "height": "70vh",
                "z-index": 999,
            },
            layout={
                "name": "preset",
                "animate": True,
                "fit": True,
                "padding": 10,
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
    # style={"width": "90vw"},
)

debug_inspector = dmc.Container(
    [
        dmc.Spoiler(
            children=[
                dmc.Prism(
                    language="json", id=ids.DEBUG_NODE_INSPECTOR_CAMPUS, children=""
                )
            ],
            showLabel="Show more",
            hideLabel="Hide",
            maxHeight=100,
        )
    ]
)

bed_inspector = html.Div(
    [
        dmc.AccordionMultiple(
            id=ids.INSPECTOR_CAMPUS_ACCORDION,
            children=[
                dmc.AccordionItem(id=ids.ACCORDION_ITEM_PATIENT, value="patient"),
                dmc.AccordionItem(id=ids.ACCORDION_ITEM_PERRT, value="bed"),
                dmc.AccordionItem(id=ids.ACCORDION_ITEM_DEBUG, value="debug"),
            ],
            chevronPosition="left",
            variant="separated",
            transitionDuration=0,
        )
    ]
)

inspector = html.Div(
    [
        dmc.Modal(
            id=ids.INSPECTOR_CAMPUS_MODAL,
            centered=True,
            padding="xs",
            size="60vw",
            overflow="inside",
            overlayColor=colors.gray,
            overlayOpacity=0.5,
            transition="fade",
            transitionDuration=0,
            children=[bed_inspector],
        )
    ]
)

body = dmc.Container(
    [
        dmc.Grid(
            [
                dmc.Col(dept_selector, span=6),
                dmc.Col(campus_selector, offset=3, span=3),
                dmc.Col(campus_status, span=12),
                dmc.Col(campus_cyto, span=12),
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
            notifications,
            body,
            inspector,
        ]
    )
