from typing import Any
import dash
import dash_mantine_components as dmc
import json
from dash import Input, Output, State, callback
from types import SimpleNamespace
from typing import Tuple

from web.pages.sitrep import ids
from web.pages.sitrep.callbacks.cytoscape import format_census

DEBUG = True


def _format_tap_node_data(data: dict | None) -> str:
    if data:
        # remove the style part of tapNode for readabilty
        data.pop("style", None)
    return json.dumps(data, indent=4)


@callback(
    [
        Output(ids.DEBUG_NODE_INSPECTOR_CAMPUS, "children"),
        Output(ids.INSPECTOR_CAMPUS, "opened"),
    ],
    Input(ids.CYTO_CAMPUS, "tapNode"),
    State(ids.INSPECTOR_CAMPUS, "opened"),
    prevent_initial_callback=True,
)
def tap_debug_inspector_campus(data: dict, opened: str) -> Tuple[str, bool]:
    if not DEBUG:
        return dash.no_update, False
    if not data:
        return _format_tap_node_data(data), False
    else:
        return _format_tap_node_data(data), not opened


def _create_accordion_item(control: Any, panel: Any) -> Any:
    return [dmc.AccordionControl(control), dmc.AccordionPanel(panel)]


@callback(
    [
        Output(ids.INSPECTOR_WARD, "opened"),
        Output(ids.DEBUG_NODE_INSPECTOR_WARD, "children"),
        Output(ids.INSPECTOR_WARD, "title"),
        Output(ids.MODAL_ACCORDION_PATIENT, "children"),
        Output(ids.MODAL_ACCORDION_BED, "children"),
    ],
    Input(ids.CYTO_WARD, "tapNode"),
    State(ids.INSPECTOR_WARD, "opened"),
    prevent_initial_callback=True,
)
def tap_inspector_ward(
    node: dict, modal_opened: str
) -> Tuple[bool, str, str, str, Any]:
    """
    Populate the bed inspector modal
    Args:
        node:
        modal_opened:

    Returns:
        modal: open status (toggle)
        debug_inspection: json formattd string
        title: title of the modal built from patient data
        patient_content: to be viewed in the modal

    """
    if not node:
        return False, dash.no_update, "", "", dash.no_update

    data = node.get("data", {})
    if data.get("entity") != "bed":
        return False, dash.no_update, "", "", dash.no_update

    occupied = data.get("occupied")

    bed = data.get("bed")
    bed_prefix = "Sideroom" if bed.get("sideroom") else "Bed"

    modal_title = f"{bed_prefix} {bed.get('bed_number')}  " f"({bed.get('department')})"
    accordion_pt_item = _create_accordion_item("🔬 Unoccupied", "")
    accordion_bed_item = _create_accordion_item("🛏 Bed status", "")

    if occupied:
        census = data.get("census")
        cfmt = SimpleNamespace(**format_census(census))
        accordion_pt_item = _create_accordion_item(
            f"🔬 {cfmt.demographic_slug}", "🚧 Patient details under construction 🚧"
        )

    return (
        not modal_opened,
        _format_tap_node_data(node),
        modal_title,
        accordion_pt_item,
        accordion_bed_item,
    )
