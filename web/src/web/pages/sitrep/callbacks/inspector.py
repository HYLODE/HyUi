import dash
import dash_mantine_components as dmc
import json
from dash import Input, Output, State, callback, callback_context
from dash_iconify import DashIconify
from typing import Any, Tuple

from web.pages.sitrep import DISCHARGE_DECISIONS, ids
from web.pages.sitrep.callbacks.cytoscape import format_census
from web.pages.sitrep.callbacks.discharges import post_discharge_status
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
def open_inspector_modal(node: dict, opened: bool) -> Tuple[bool, list[str], dmc.Group]:
    """
    Open modal
    prepare modal title
    define which accordion item is open
    """
    if not node:
        return False, ["bed"], dmc.Group()

    data = node.get("data", {})
    if data.get("entity") != "bed":
        return False, ["bed"], dmc.Group()

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


@callback(
    Output(ids.ACCORDION_ITEM_BED, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
    Input(ids.INSPECTOR_WARD_MODAL, "opened"),
    prevent_initial_call=True,
)
def bed_accordion_item(
    node: dict, modal_open: bool
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for bed accordion item"""
    if not node or not modal_open:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    data = node.get("data", {})
    bed_status_control_value = data.get("dc_status", "").upper()

    # BUG?: SegmentedControl does not reset to original colors after first draw
    color = "indigo" if bed_status_control_value else "gray"

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
                    data=[i.get("label") for i in DISCHARGE_DECISIONS],
                    fullWidth=True,
                    value=bed_status_control_value,
                    color=color,
                    persistence=False,
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
    description = [
        i.get("description", "") for i in DISCHARGE_DECISIONS if i.get("label") == value
    ]
    if description:
        return description[0]
    else:
        return "Choose one"


@callback(
    [
        Output(ids.ACC_BED_SUBMIT_WARD_NOTIFY, "children"),
        Output(ids.ACC_BED_SUBMIT_WARD, "disabled"),
        Output(ids.ACC_BED_SUBMIT_STORE, "data"),
    ],
    Input(ids.ACC_BED_SUBMIT_WARD, "n_clicks"),
    Input(ids.ACC_BED_STATUS_WARD, "value"),
    State(ids.ACC_BED_SUBMIT_WARD, "disabled"),
    State(ids.CYTO_WARD, "tapNode"),
    prevent_initial_call=True,
)
def submit_discharge_status(
    _: int,
    value: str,
    disabled: bool,
    node: dict,
) -> Tuple[dmc.Notification, bool, dict]:
    """Handle the submission of new info"""

    msg = ""
    data = node.get("data", {})
    status = value.lower()
    response_status = -1
    response_dict = {}

    if callback_context.triggered_id == ids.ACC_BED_STATUS_WARD:
        bed_status_control_value = data.get("dc_status", "").upper()
        disabled = True if bed_status_control_value == status else False
        show = False
    elif callback_context.triggered_id == ids.ACC_BED_SUBMIT_WARD:
        if status != "blocked":
            encounter = int(data.get("encounter", -1))
            response_status, response_json = post_discharge_status(
                csn=encounter, status=value
            )
            response_dict = response_json.dict()
            if response_status == 200:
                msg = "Updated discharge status: OK"
                disabled = True
            else:
                msg = "Uh-oh: Unable to save discharge status - try again?"
                disabled = False

        show = True
    else:
        disabled = False
        show = False

    if show:
        show_arg = "show" if show else "hide"

        bed_submit_dict = dict(
            msg=msg,
            status=status.lower(),
            id=data.get("id"),
            response_json=response_dict,
            response_status=response_status,
        )

        notificaton = dmc.Notification(
            title="Saving discharge status",
            id="_submit_discharge_status_notification_NOT_IN_USE",
            action=show_arg,
            message=msg,
            icon=DashIconify(icon="ic:round-celebration"),
        )

        return notificaton, disabled, bed_submit_dict

    else:
        return dash.no_update, disabled, dash.no_update


@callback(
    Output(ids.ACCORDION_ITEM_PATIENT, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
    Input(ids.INSPECTOR_WARD_MODAL, "opened"),
    prevent_initial_call=True,
)
def patient_accordion_item(
    node: dict, modal_open: bool
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for bed accordion item"""
    if not node or not modal_open:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    data = node.get("data", {})
    census = data.get("census", {})
    occupied = census.get("occupied", False)
    sex_icon = "carbon:person"
    control_text = "Unoccupied"
    if census and occupied:
        censusf = format_census(census)
        sex = censusf.get("sex", "")
        if sex:
            sex_icon = "carbon:male" if sex.lower() == "m" else "carbon:female"
        control_text = censusf.get("demographic_slug", "Uh-oh! No patient data?")

    control = dmc.Group(
        [
            DashIconify(
                icon=sex_icon,
                width=20,
            ),
            dmc.Text(control_text),
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
            maxHeight=200,
        )
    )
    return control, panel
