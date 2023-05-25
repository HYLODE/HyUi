import dash
import dash_mantine_components as dmc
import json
from dash import html, dcc
from pathlib import Path

import web.pages.sitrep.callbacks.abacus  # noqa

from web.pages.sitrep import ids, CAMPUSES
from web.style import replace_colors_in_stylesheet

dash.register_page(__name__, path="/sitrep/abacus", name="Abacus")

with open(Path(__file__).parent / "abacus_style.json") as f:
    abacus_style = json.load(f)
    abacus_style = replace_colors_in_stylesheet(abacus_style)

timers = html.Div([])
stores = html.Div([])

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

with open(Path(__file__).parent.parent / "electives/model.md") as f:
    elective_markdown = f.read()

elective_model_card = dmc.Modal(
    children=dcc.Markdown(elective_markdown),
    id="model_card",
    size="40%",
    opened=False,
)

elective_card_button = dmc.Button(
    id="electives_button", children="Electives Model Info", color="blue", fullWidth=True
)


body = dmc.Container(
    [
        dmc.Grid(
            [
                # dmc.Col(campus_selector, span=3),
                # dmc.Col(elective_card_button, span=3),
                # dmc.Col(emergency_card_button, span=3),
                # dmc.Col(discharge_card_button, span=3),
                # dmc.Col(now_progress_bar, span=12),
                # dmc.Col(mane_progress_bar, span=12),
                # dmc.Col(elective_adjustor, span=3),
                # dmc.Col(elective_graph, span=3),
                # dmc.Col(emergency_adjustor, span=3),
                # dmc.Col(emergency_graph, span=3),
                # dmc.Col(discharge_adjustor, span=3),
                # dmc.Col(discharge_graph, span=3),
                # dmc.Col(overall_graph, span=3),
                # dmc.Col(abacus, span=12),
                # dmc.Col(elective_model_card),
                # dmc.Col(emergency_model_card),
                # dmc.Col(discharges_model_card),
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
