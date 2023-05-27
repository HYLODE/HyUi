import dash
import dash_mantine_components as dmc

# import dash_cytoscape as cyto

import json
from dash import html, dcc, dash_table as dtable
from pathlib import Path
from dash_iconify import DashIconify

# import plotly.express as px

from web.pages.sitrep.icus import ward_cyto, ward_list

# from web.pages.electives.electives import electives_list

import web.pages.sitrep.callbacks.abacus  # noqa
import web.pages.sitrep.callbacks.widgets  # noqa
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

dash.register_page(__name__, path="/sitrep/abacus", name="Abacus")
# with open(Path(__file__).parent / "cyto_style_icus.json") as f:
#     cyto_style_sheet = json.load(f)
#     cyto_style_sheet = replace_colors_in_stylesheet(cyto_style_sheet)

with open(Path(__file__).parent / "abacus_style.json") as f:
    abacus_style = json.load(f)
    abacus_style = replace_colors_in_stylesheet(abacus_style)

with open(Path(__file__).parent.parent / "electives/table_style_sheet.json") as f:
    table_style_sheet = json.load(f)
    table_style_sheet = replace_colors_in_stylesheet(table_style_sheet)


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

electives_list = dmc.Paper(
    dtable.DataTable(
        id="electives_list",
        columns=[
            {"id": "pacu_yn", "name": "PACU"},
            {"id": "full_name", "name": "Full Name"},
            {"id": "age_sex", "name": "Age / Sex"},
        ],
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


class AbacusTap:
    def __init__(
        self,
        category: str,
        card_path: Path,
        adj_description: str,
        icon: str,
        color: tuple,
    ):
        self.category = category
        self.model_card_id = f"{category}_model_card"
        self.card_button_id = f"{category}_button"
        self.adjustor_id = f"{category}_adjustor"
        self.graph_id = f"{category}_graph"

        with open(card_path) as f:
            markdown = f.read()

        self.model_card = dmc.Modal(
            children=dcc.Markdown(markdown),
            id=self.model_card_id,
            size="40%",
            opened=False,
        )

        self.card_button = dmc.Button(
            id=self.card_button_id,
            children=f"{category.capitalize()} Model Info",
            # color = "blue",
            style={
                "background-color": f"rgb({color[0]},{color[1]},{color[2]},1",
                "color": "black",
            },
            fullWidth=True,
        )

        self.adjustor = dmc.Slider(
            id=self.adjustor_id,
            style={"width": "100%"},
            min=0,
            max=8,
            labelAlwaysOn=1,
        )

        self.graph = dcc.Graph(id=self.graph_id)

        self.adj_graph = dmc.Paper(
            [
                dmc.Grid(
                    [
                        dmc.Col(DashIconify(icon=icon), span=2),
                        dmc.Col(
                            dmc.Text(
                                category.capitalize(),
                                align="right",
                                id=f"{category}_title",
                            ),
                            span=10,
                        ),
                        dmc.Col(self.adjustor, span=12),
                        dmc.Col(self.graph, span=12),
                    ]
                )
            ],
            shadow="xs",
            p="sm",
            withBorder=True,
            style={"background-color": f"rgb({color[0]},{color[1]},{color[2]},0.5)"},
        )


elective_tap = AbacusTap(
    "electives",
    card_path=(Path(__file__).parent.parent / "electives/model.md"),
    adj_description="Expected ICU admissions from Elective Surgeries",
    icon="carbon:calendar",
    color=(18, 184, 134),  # green
)

emergency_tap = AbacusTap(
    "emergencies",
    card_path=(Path(__file__).parent / "emergency_model.md"),
    adj_description="Expected ICU admissions from A&E and the wards",
    icon="carbon:stethoscope",
    color=(250, 82, 82),  # red
)

discharge_tap = AbacusTap(
    "discharges",
    card_path=(Path(__file__).parent / "discharge_model.md"),
    adj_description="Expected ICU discharges",
    icon="carbon:home",
    color=(190, 75, 219),  # purple
)


now_progress_bar = dmc.Progress(
    id=ids.PROGRESS_WARD,
    size="xl",
    radius="md",
)


mane_progress_bar = dmc.Progress(
    id="mane_progress_bar",
    size="xl",
    radius="md",
)

overall_graph = dmc.Paper(
    children=[
        # dmc.Text("Overall ICU Occupancy Tomorrow", size="lg"),
        dcc.Graph(id="overall_graph"),
    ],
    shadow="sm",
    p="xs",
    withBorder=True,
)

# adjustors = dmc.Paper(
#     p="sm",
#     shadow="xs",
#     withBorder=True,
#     children=[dmc.Grid([dmc.Col(elective_tap.adjustor, span=4),
#                         dmc.Col(emergency_tap.adjustor, span=4),
#                         dmc.Col(discharge_tap.adjustor, span=4)])],
# )

body = dmc.Container(
    [
        dmc.Grid(
            [
                dmc.Col(dept_selector, span=4),
                dmc.Col(elective_tap.card_button, span=2, offset=2),
                dmc.Col(emergency_tap.card_button, span=2),
                dmc.Col(discharge_tap.card_button, span=2),
                dmc.Col(dmc.Text("Now: "), span=1),
                dmc.Col(now_progress_bar, span=11),
                dmc.Col(dmc.Text("Tomorrow: "), span=1),
                dmc.Col(mane_progress_bar, span=11),
                dmc.Col(overall_graph, span=11, offset=1),
                dmc.Col(elective_tap.adj_graph, span=4),
                dmc.Col(emergency_tap.adj_graph, span=4),
                dmc.Col(discharge_tap.adj_graph, span=4),
                dmc.Col(electives_list, span=3),
                dmc.Col(ward_cyto, span=6),
                dmc.Col(ward_list, span=3),
                dmc.Col(elective_tap.model_card),
                dmc.Col(emergency_tap.model_card),
                dmc.Col(discharge_tap.model_card),
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
        ]
    )
