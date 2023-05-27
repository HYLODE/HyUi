# import requests

import numpy as np
from dash import Input, Output, State, callback
from web.pages.sitrep import ids

# from web.stores import ids as store_ids
# from web.convert import parse_to_data_frame
# from models.electives import MergedData

from web.pages.sitrep.callbacks.abacus_funcs import (
    Abacus,
    BED_NUMBERS,
)

abaci = {}
for dept in BED_NUMBERS.keys():
    abaci[dept] = Abacus(dept)


@callback(
    Output("overall_graph", "figure"),
    Input(ids.DEPT_SELECTOR, "value"),
)
def overall_graph(
    dept: str,
) -> dict:
    return abaci[dept].overall_graph


def create_callback(tap: str) -> tuple:
    @callback(
        Output(f"{tap}_model_card", "opened"),
        Input(f"{tap}_button", "n_clicks"),
        State(f"{tap}_model_card", "opened"),
        prevent_initial_call=True,
    )
    def _modal(_: int, opened: bool) -> bool:
        return not opened

    @callback(
        Output(f"{tap}_graph", "figure"),
        Input(ids.DEPT_SELECTOR, "value"),
        Input(f"{tap}_adjustor", "value"),
    )
    def _show_graph(dept: str, adj_value: int):  # type: ignore
        abacus_instance = abaci[dept]
        tap_data = getattr(abacus_instance, f"{tap}_pmf")
        return abacus_instance.generate_graph(tap, tap_data, adj_value)

    @callback(
        Output(f"{tap}_adjustor", "value"),
        Output(f"{tap}_adjustor", "max"),
        Input(ids.DEPT_SELECTOR, "value"),
    )
    def _set_adjustor(dept: str) -> tuple:
        abacus_instance = abaci[dept]
        max_prob_index = np.argmax(np.abs(getattr(abacus_instance, f"{tap}_pmf")))
        return (
            max_prob_index,
            abacus_instance.total_beds,
        )

    return _modal, _show_graph, _set_adjustor


for tap in ["electives", "emergencies", "discharges"]:
    modal_callback, show_graph_callback, adjustor_callback = create_callback(tap)


@callback(
    Output("mane_progress_bar", "sections"),
    Output("mane_progress_bar", "max"),
    Output(ids.PROGRESS_WARD, "max"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input("electives_adjustor", "value"),
    Input("emergencies_adjustor", "value"),
    Input("discharges_adjustor", "value"),
)
def mane_progress_bar(
    dept: str,
    electives: int,
    emergencies: int,
    discharges: int,
) -> tuple:
    abacus_instance = abaci[dept]

    n_beds = abacus_instance.occupied_beds
    expected_beds = n_beds - discharges
    total_beds = abacus_instance.total_beds

    admitted_element = {
        "value": (expected_beds / total_beds) * 100,
        "color": "blue",
        "label": f"{expected_beds} staying in",
    }
    elective_element = {
        "value": (electives / total_beds) * 100,
        "color": "green",
        "label": f"{electives} Electives",
    }
    emergency_element = {
        "value": (emergencies / total_beds) * 100,
        "color": "red",
        "label": f"{emergencies} Emergencies",
    }

    return (
        [admitted_element, elective_element, emergency_element],
        total_beds,
        total_beds,
    )
