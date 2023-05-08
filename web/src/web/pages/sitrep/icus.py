import dash
import dash_cytoscape as cyto
import dash_mantine_components as dmc
import json
from dash import dcc, html
from pathlib import Path

import web.pages.sitrep.layouts.bedlist  # noqa

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks.cytoscape  # noqa
import web.pages.sitrep.callbacks.discharges  # noqa
import web.pages.sitrep.callbacks.inspector  # noqa
import web.pages.sitrep.callbacks.widgets  # noqa
import web.pages.sitrep.callbacks.sitrep  # noqa
import web.pages.sitrep.callbacks.census  # noqa
import web.pages.sitrep.callbacks.beds  # noqa
import web.pages.sitrep.callbacks.hymind  # noqa
from web.pages.sitrep import ids
from web import SITREP_DEPT2WARD_MAPPING
from web.style import replace_colors_in_stylesheet

dash.register_page(__name__, path="/sitrep/icus", name="Critical Care")

with open(Path(__file__).parent / "cyto_style_icus.json") as f:
    cyto_style_sheet = json.load(f)
    cyto_style_sheet = replace_colors_in_stylesheet(cyto_style_sheet)

timers = html.Div([])

stores = html.Div(
    [
        html.Data(id=ids.DEPT_GROUPER, value="ALL_ICUS", hidden=True),
        dcc.Store(id=ids.CENSUS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE),
        dcc.Store(id=ids.ROOMS_OPEN_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.DEPTS_OPEN_STORE_NAMES),
        dcc.Store(id=ids.SITREP_STORE),
        dcc.Store(id=ids.HYMIND_DC_STORE),
        dcc.Store(id=ids.DISCHARGES_STORE),
        dcc.Store(id=ids.ACC_BED_SUBMIT_STORE),
    ]
)

notifications = html.Div(
    [
        html.Div(id=ids.ACC_BED_SUBMIT_WARD_NOTIFY),
    ]
)

dept_selector = dmc.Container(
    [
        dmc.SegmentedControl(
            id=ids.DEPT_SELECTOR,
            value="UCH T03 INTENSIVE CARE",
            data=[
                {"value": k, "label": v}
                for k, v in list(SITREP_DEPT2WARD_MAPPING.items())
            ],
            persistence=True,
            persistence_type="local",
        ),
    ],
    fluid=True,
    p="xxs",
)

ward_status = dmc.Paper(
    [
        dmc.Progress(
            id=ids.PROGRESS_WARD,
            size=20,
            radius="md",
        )
    ],
)

ward_cyto = dmc.Paper(
    [
        cyto.Cytoscape(
            id=ids.CYTO_WARD,
            style={
                # "width": "70vw",  # do not set width; will derive from height
                "height": "50vh",
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
    p="xs",  # padding
    withBorder=True,
)

ward_list = dmc.Paper(
    # Todo: convert to using datatable
    dmc.Table(
        id=ids.BED_SELECTOR_WARD,
        striped=True,
        highlightOnHover=True,
        verticalSpacing="xxs",
        horizontalSpacing="md",
    ),
    shadow="lg",
    radius="lg",
    p="xs",  # padding
    withBorder=True,
)

debug_inspector = dmc.Container(
    [
        dmc.Spoiler(
            children=[
                dmc.Prism(
                    language="json", id=ids.DEBUG_NODE_INSPECTOR_WARD, children=""
                )
            ],
            showLabel="Show more",
            hideLabel="Hide",
            maxHeight=100,
        )
    ]
)

sidebar_title = html.Div(id=ids.INSPECTOR_WARD_TITLE)

# use html.div to allow the bed inspector to be hidden by settinging the hidden
# property boolean
sidebar = html.Div(
    children=[
        sidebar_title,
        html.Div(
            id=ids.INSPECTOR_WARD_SIDEBAR,
            children=[
                dmc.AccordionMultiple(
                    id=ids.INSPECTOR_WARD_ACCORDION,
                    children=[
                        dmc.AccordionItem(
                            id=ids.ACCORDION_ITEM_PATIENT, value="patient"
                        ),
                        dmc.AccordionItem(id=ids.ACCORDION_ITEM_BED, value="bed"),
                        dmc.AccordionItem(id=ids.ACCORDION_ITEM_DEBUG, value="debug"),
                    ],
                    chevronPosition="left",
                    variant="separated",
                    transitionDuration=0,
                ),
            ],
        ),
    ],
)

patient_sidebar = dmc.Container(
    dmc.Paper(
        shadow="lg",
        radius="lg",
        p="xs",  # padding
        withBorder=True,
        children=[sidebar],
    )
)

body = dmc.Container(
    [
        dmc.Grid(
            [
                dmc.Col(dept_selector, span=3),
                dmc.Col([], span=6, offset=3),
                dmc.Col(ward_status, span=12),
                dmc.Col(ward_list, span=3),
                # nested grid
                dmc.Col(
                    dmc.Grid(
                        [
                            # dmc.Col(dmc.Text("Hello World", span=12)),
                            dmc.Col(ward_cyto, span=12),
                        ]
                    ),
                    span=4,
                ),
                dmc.Col(dmc.Grid([dmc.Col(patient_sidebar, span=12)]), span=5),
            ]
        )
    ],
    size="xl",
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            notifications,
            body,
        ]
    )
