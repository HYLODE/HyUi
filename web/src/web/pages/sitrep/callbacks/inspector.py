from datetime import datetime
import dash
import dash_mantine_components as dmc
import json
from dash import Input, Output, State, callback, callback_context, html
from dash_iconify import DashIconify
from typing import Any, Tuple

from web.pages.sitrep import DISCHARGE_DECISIONS, ids
from web.pages.sitrep.callbacks.census import format_census
from web.pages.sitrep.callbacks.discharges import post_discharge_status
from web.pages.sitrep.callbacks.utils import make_sitrep_badge
from web.style import colors

DEBUG = True


def _report_patient_status(sitrep: dict) -> dmc.Group:
    resp_badge = make_sitrep_badge("vent_type_1_4h", sitrep)
    cvs_badge = make_sitrep_badge("n_inotropes_1_4h", sitrep)
    rrt_badge = make_sitrep_badge("had_rrt_1_4h", sitrep)
    delirium_badge = make_sitrep_badge("is_agitated_1_8h", sitrep)

    return dmc.Group(
        [
            resp_badge,
            cvs_badge,
            rrt_badge,
            delirium_badge,
        ]
    )


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
        Output(ids.INSPECTOR_WARD_SIDEBAR, "hidden"),
        Output(ids.INSPECTOR_WARD_ACCORDION, "value"),
        Output(ids.INSPECTOR_WARD_TITLE, "children"),
    ],
    Input(ids.CYTO_WARD, "selectedNodeData"),
    Input(ids.DEPT_SELECTOR, "value"),
    prevent_initial_callback=True,
)
def update_patient_sidebar(
    nodes: list[dict], _: str
) -> Tuple[bool, list[str], dmc.Group]:
    """Update sidebar"""

    click_title = dmc.Group(
        [
            DashIconify(
                icon="material-symbols:left-click-rounded",
                color=colors.indigo,
                width=30,
            ),
            dmc.Text(f"Click on a bed for more information", weight=500),
        ]
    )

    if (
        not nodes
        or len(nodes) != 1
        or callback_context.triggered_id == ids.DEPT_SELECTOR
    ):
        return True, [], dmc.Group(click_title)

    data = nodes[0]
    if data.get("entity") != "bed":
        return True, ["bed"], dmc.Group(click_title)

    bed = data.get("bed")
    bed_color = colors.orange if data.get("occupied") else colors.gray
    bed_number = bed.get("bed_number")
    department = bed.get("department")

    bed_title = dmc.Group(
        [
            DashIconify(
                icon="carbon:hospital-bed",
                color=bed_color,
                width=30,
            ),
            dmc.Text(f"BED {bed_number}", weight=500),
            dmc.Text(f"{department}", color=colors.gray),
        ],
        pb=20,
    )

    return False, ["patient", "bed"], bed_title


@callback(
    Output(ids.ACCORDION_ITEM_BED, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
    prevent_initial_call=True,
)
def bed_accordion_item(
    node: dict,
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for bed accordion item"""
    if not node:
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
            dmc.Text("Discharge decision", size="sm"),
        ]
    )
    panel = dmc.Grid(
        [
            dmc.Col(
                [
                    dmc.Text(
                        "Ready for discharge/transfer/step-down etc.",
                        color=colors.gray,
                        size="sm",
                    )
                ],
                span=12,
            ),
            dmc.Col(
                dmc.SegmentedControl(
                    id=ids.ACC_BED_STATUS_WARD,
                    data=[i.get("label") for i in DISCHARGE_DECISIONS],
                    fullWidth=True,
                    value=bed_status_control_value,
                    color=color,
                    persistence=False,
                    size="sm",
                ),
                span=12,
            ),
            dmc.Col(
                [dmc.Text(id=ids.ACC_BED_DECISION_TEXT, size="sm", color=colors.gray)],
                span=6,
            ),
            dmc.Col(
                dmc.Button(
                    "Submit",
                    id=ids.ACC_BED_SUBMIT_WARD,
                    color="orange",
                    size="sm",
                    # variant="default",
                ),
                span="content",
            ),
        ],
        justify="space-between",
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
            icon=DashIconify(icon="carbon:checkmark-outline"),
            autoClose=1500,
            color=colors.green,
        )

        return notificaton, disabled, bed_submit_dict

    else:
        return dash.no_update, disabled, dash.no_update


@callback(
    Output(ids.ACCORDION_ITEM_PATIENT, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
    prevent_initial_call=True,
)
def patient_accordion_item(
    node: dict,
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for patient accordion item"""
    if not node:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    data = node.get("data", {})

    if data.get("closed"):
        control = dmc.Group(
            [
                DashIconify(
                    icon="carbon:close-outline",
                    width=20,
                ),
                dmc.Text("Bed closed", size="sm"),
            ]
        )
        panel = None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    census = data.get("census", {})
    occupied = census.get("occupied", False)
    sex_icon = "carbon:person"
    control_text = "Unoccupied"
    if census and occupied:
        censusf = format_census(census)
        sex = censusf.get("sex", "")
        if sex:
            sex_icon = (
                "carbon:gender-male" if sex.lower() == "m" else "carbon:gender-female"
            )
        control_text = "{firstname} {lastname} ({age}yrs)".format(**censusf)

    control = dmc.Group(
        [
            DashIconify(
                icon=sex_icon,
                width=20,
            ),
            dmc.Text(control_text, size="sm"),
        ]
    )

    sitrep = data.get("sitrep", {})
    if sitrep:
        dob = dmc.Code(censusf.get("dob_fshort", "DD-MM-CCYY"), block=False)
        mrn = dmc.Code(censusf.get("mrn", "Unknown"), block=False)
        csn = dmc.Code(censusf.get("encounter", "Unknown"), block=False)
        ids_labels = html.Tr([html.Td("DoB"), html.Td("MRN"), html.Td("CSN")])
        ids_row = html.Tr([html.Td(dob), html.Td(mrn), html.Td(csn)])
        ids_body = html.Tbody([ids_labels, ids_row])
        ids_table = dmc.Table([ids_body])

        try:
            hospital_admit = census.get("hv_admission_dt")
            hospital_los = str(int((datetime.utcnow() - hospital_admit).days))
            hospital_admit_str = datetime.strftime(hospital_admit, "%d %b %Y")
            los_text = dmc.Text(f"Hospital LoS: {hospital_los}", size="sm")
        except TypeError as e:
            los_text = dmc.Text(f"Hospital LoS: Unknown", size="sm")

        sitrep_content = [
            _report_patient_status(sitrep),
            ids_table,
            los_text,
        ]
    else:
        sitrep_content = [dmc.Text("Sitrep patient data not available", size="sm")]

    panel = dmc.Grid(
        [
            dmc.Col(
                sitrep_content,
                span=12,
            )
        ]
    )

    return dmc.AccordionControl(control), dmc.AccordionPanel(panel)


@callback(
    Output(ids.ACCORDION_ITEM_DEBUG, "children"),
    Input(ids.CYTO_WARD, "tapNode"),
)
def debug_accordion_item(node: dict) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for debug accordion item"""
    if not node:
        control, panel = None, None
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    title = dmc.Group(
        [
            DashIconify(
                icon="carbon:debug",
                width=20,
            ),
            dmc.Text("Developer and debug inspector", size="xs"),
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
