import dash_mantine_components as dmc
import json
from dash import Input, Output, State, callback
from dash_iconify import DashIconify
from typing import Any, Tuple

from web.pages.sitrep import ids
from web.pages.sitrep.callbacks.cytoscape import format_census
from web.style import colors

DEBUG = True


def _format_tapnode(data: dict | None) -> str:
    """JSON dump of data from node (for debugging inspector"""
    if data:
        # remove the style part of tapNode for readabilty
        data.pop("style", None)
    return json.dumps(data, indent=4)


def _create_accordion_item(control: Any, panel: Any) -> Any:
    return [dmc.AccordionControl(control), dmc.AccordionPanel(panel)]


@callback(
    [
        Output(ids.INSPECTOR_WARD_MODAL, "opened"),
        Output(ids.INSPECTOR_WARD_ACCORDION, "value"),
        Output(ids.INSPECTOR_WARD_MODAL, "title"),
    ],
    Input(ids.CYTO_WARD, "tapNode"),
    State(ids.INSPECTOR_WARD_MODAL, "opened"),
    prevent_initial_callback=True,
)
def open_inspector_modal(node: dict, opened: bool) -> Tuple[bool, list[str], str]:
    """
    Open modal
    prepare modal title
    define which accordion item is open
    """
    if not node:
        return False, ["bed"], ""

    data = node.get("data", {})
    if data.get("entity") != "bed":
        return False, ["bed"], ""

    bed = data.get("bed")
    bed_color = colors.orange if data.get("occupied") else colors.gray
    bed_number = bed.get("bed_number")
    department = bed.get("department")
    # room = bed.get("room")
    # room_type = "Sideroom" if data.get("room", {}).get("is_sidroom") else
    # "Bay"

    modal_title = dmc.Group(
        [
            DashIconify(
                icon="carbon:hospital-bed",
                color=bed_color,
                width=30,
            ),
            dmc.Text(f"BED {bed_number}", weight=500),
            dmc.Text(f"{department}", color=colors.gray),
        ]
    )

    return not opened, ["bed"], modal_title


decisions = [
    dict(label="HOLD", description="Not for discharge"),
    dict(label="REVIEW", description="Review for possible discharge later"),
    dict(label="DISCHARGE", description="Ready for discharge now"),
    dict(label="EXCELLENCE", description="Excellence in the End of Life " "pathway"),
    dict(
        label="BLOCKED", description="Block the bed (not available for " "admissions)"
    ),
]


@callback(
    Output(ids.ACCORDION_ITEM_BED, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
)
def bed_accordion_item(node: dict) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for bed accordion item"""
    if not node:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    # data = node.get("data", {})

    control = dmc.Group(
        [
            DashIconify(
                icon="carbon:logout",
                width=20,
            ),
            dmc.Text("Discharge decision"),
        ]
    )
    panel = dmc.Grid(
        [
            dmc.Col(
                dmc.SegmentedControl(
                    id=ids.ACC_BED_STATUS_WARD,
                    data=[i.get("label") for i in decisions],
                    fullWidth=True,
                    value="",
                    color="indigo",
                ),
                span=9,
            ),
            dmc.Col(
                dmc.Button(
                    "Submit",
                    id=ids.ACC_BED_SUBMIT_WARD,
                    color="orange",
                    # variant="default",
                ),
                offset=1,
                span=2,
            ),
            dmc.Col(
                [dmc.Text(id=ids.ACC_BED_DECISION_TEXT, color=colors.gray)],
                span=12,
            ),
        ]
    )

    return dmc.AccordionControl(control), dmc.AccordionPanel(panel)


@callback(
    Output(ids.ACC_BED_DECISION_TEXT, "children"),
    Input(ids.ACC_BED_STATUS_WARD, "value"),
)
def update_decision_description(value: str) -> str:
    description = [i.get("description") for i in decisions if i.get("label") == value]
    if description:
        return description[0]
    else:
        return "Choose one"


@callback(
    Output(ids.ACCORDION_ITEM_PATIENT, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
)
def patient_accordion_item(
    node: dict,
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for patient accordion item"""
    if not node:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    data = node.get("data", {})
    census = data.get("census", {})
    censusf = format_census(census)

    sex = census.get("sex", "")
    if sex is None:
        sex_icon = "carbon:person"
    else:
        sex_icon = "carbon:male" if sex.lower() == "m" else "carbon:female"

    control = dmc.Group(
        [
            DashIconify(
                icon=sex_icon,
                width=20,
            ),
            dmc.Text(censusf.get("demographic_slug")),
        ]
    )
    panel = dmc.Group()

    return dmc.AccordionControl(control), dmc.AccordionPanel(panel)


@callback(
    Output(ids.ACCORDION_ITEM_DEBUG, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
)
def debug_accordion_item(node: dict) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for debug accordion item"""
    title = dmc.Group(
        [
            DashIconify(
                icon="carbon:debug",
                width=20,
            ),
            dmc.Text("Developer and debug inspector"),
        ]
    )
    control = dmc.AccordionControl(title)
    panel = dmc.AccordionPanel(
        dmc.Spoiler(
            children=[
                dmc.Prism(
                    language="json",
                    children=_format_tapnode(node),
                )
            ],
            showLabel="Show more",
            hideLabel="Hide",
            maxHeight=100,
        )
    )
    return control, panel


# @callback(
#     [
#         Output(ids.INSPECTOR_WARD, "opened"),
#         Output(ids.DEBUG_NODE_INSPECTOR_WARD, "children"),
#         Output(ids.INSPECTOR_WARD, "title"),
#         Output(ids.MODAL_ACCORDION_PATIENT, "children"),
#         Output(ids.MODAL_ACCORDION_BED, "children"),
#     ],
#     Input(ids.CYTO_WARD, "tapNode"),
#     State(ids.INSPECTOR_WARD, "opened"),
#     prevent_initial_callback=True,
# )
# def tap_inspector_ward(
#     node: dict, modal_opened: str
# ) -> Tuple[bool, str, str, str, Any]:
#     """
#     Populate the bed inspector modal
#     Args:
#         node:
#         modal_opened:
#
#     Returns:
#         modal: open status (toggle)
#         debug_inspection: json formattd string
#         title: title of the modal built from patient data
#         patient_content: to be viewed in the modal
#
#     """
#     if not node:
#         return False, dash.no_update, "", "", dash.no_update
#
#     data = node.get("data", {})
#     if data.get("entity") != "bed":
#         return False, dash.no_update, "", "", dash.no_update
#
#     occupied = data.get("occupied")
#
#     bed = data.get("bed")
#     bed_prefix = "Sideroom" if bed.get("sideroom") else "Bed"
#
#     modal_title = f"{bed_prefix} {bed.get('bed_number')}  " f"({bed.get(
#     'department')})"
#     accordion_pt_item = _create_accordion_item("🔬 Unoccupied", "")
#     accordion_bed_item = _create_accordion_item("🛏 Bed status", "")
#
#     if occupied:
#         census = data.get("census")
#         cfmt = SimpleNamespace(**format_census(census))
#         accordion_pt_item = _create_accordion_item(
#             f"🔬 {cfmt.demographic_slug}", "🚧 Patient details under
#             construction 🚧"
#         )
#
#     return (
#         not modal_opened,
#         _format_tap_node_data(node),
#         modal_title,
#         accordion_pt_item,
#         accordion_bed_item,
#     )
