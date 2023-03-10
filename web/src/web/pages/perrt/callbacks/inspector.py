import dash
import dash_mantine_components as dmc
import json
from dash import Input, Output, State, callback, callback_context
from dash_iconify import DashIconify
from typing import Any, Tuple
from datetime import datetime

from web.pages.perrt import DISCHARGE_DECISIONS, ids
from web.pages.perrt.callbacks.cytoscape import format_census
from web.pages.perrt.callbacks.discharges import post_discharge_status
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
        Output(ids.SIDEBAR_CONTENT, "hidden"),
        Output(ids.INSPECTOR_CAMPUS_ACCORDION, "value"),
        Output(ids.SIDEBAR_TITLE, "children"),
    ],
    Input(ids.CYTO_CAMPUS, "selectedNodeData"),
    prevent_initial_callback=True,
)
def update_patient_sidebar(nodes: list[dict]) -> Tuple[bool, list[str], dmc.Group]:
    """
    Open modal
    prepare modal title
    define which accordion item is open
    """
    click_title = dmc.Group(
        [
            DashIconify(
                icon="material-symbols:left-click-rounded",
                color=colors.indigo,
                width=30,
            ),
            dmc.Text("Click on a bed for more information", weight=500),
        ]
    )

    if not nodes or len(nodes) != 1:
        return True, [], dmc.Group(click_title)

    data = nodes[0]
    if data.get("entity") != "bed":
        return True, ["bed"], dmc.Group(click_title)

    bed = data.get("bed")  # type: ignore
    bed_color = colors.orange if data.get("occupied") else colors.gray
    bed_number = bed.get("bed_number")  # type: ignore
    department = bed.get("department")  # type: ignore

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

    return False, ["bed"], bed_title


@callback(
    Output(ids.ACCORDION_ITEM_PERRT, "children"),
    Input(ids.CYTO_CAMPUS, "selectedNodeData"),
    prevent_initial_call=True,
)
def perrt_accordion_item(
    nodes: list[dict],
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for PERRT accordion item"""
    control, panel = None, None
    if not nodes or len(nodes) != 1:
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    data = nodes[0]
    if data.get("entity") != "bed":
        return dmc.AccordionControl(control), dmc.AccordionPanel(panel)

    news = data.get("news", {})
    admission_prediction = data.get("admission_prediction", {})

    if admission_prediction:
        pred_text = dmc.Text("ICU admission probability")
        pred_content = dmc.Group(
            dmc.Badge(
                f"{round(100 * admission_prediction)}%",
                color="orange",
                variant="filled",
            )
        )
    else:
        pred_text = dmc.Text("ICU admission probability not available")
        pred_content = dmc.Group()

    if news:
        news_text = dmc.Text("Highest/lowest vitals within the last 6 hours")
        news_content = dmc.Group(
            [
                dmc.Stack(
                    [
                        dmc.Badge("HR", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            news.get("pulse_max"), color=colors.indigo, variant="filled"
                        ),
                        dmc.Badge(
                            news.get("pulse_min"), color=colors.indigo, variant="filled"
                        ),
                    ]
                ),
                dmc.Stack(
                    [
                        dmc.Badge("RR", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            news.get("resp_max"), color=colors.indigo, variant="filled"
                        ),
                        dmc.Badge(
                            news.get("resp_min"), color=colors.indigo, variant="filled"
                        ),
                    ]
                ),
                dmc.Stack(
                    [
                        dmc.Badge("BP", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            news.get("bp_max"), color=colors.indigo, variant="filled"
                        ),
                        dmc.Badge(
                            news.get("bp_min"), color=colors.indigo, variant="filled"
                        ),
                    ]
                ),
                dmc.Stack(
                    [
                        dmc.Badge("SpO2", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            news.get("spo2_max"), color=colors.indigo, variant="filled"
                        ),
                        dmc.Badge(
                            news.get("spo2_min"), color=colors.indigo, variant="filled"
                        ),
                    ]
                ),
                dmc.Stack(
                    [
                        dmc.Badge("Temp", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            round(news.get("temp_max"), 1),
                            color=colors.indigo,
                            variant="filled",
                        ),
                        dmc.Badge(
                            round(news.get("temp_min"), 1),
                            color=colors.indigo,
                            variant="filled",
                        ),
                    ]
                ),
                dmc.Stack(
                    [
                        dmc.Badge("AVPU", color=colors.indigo, variant="outline"),
                        dmc.Badge(
                            news.get("avpu_max"), color=colors.indigo, variant="filled"
                        ),
                        dmc.Badge(
                            news.get("avpu_min"), color=colors.indigo, variant="filled"
                        ),
                    ]
                ),
            ]
        )

    else:
        news_content = dmc.Group()
        news_text = dmc.Text("Vitals not available")

    control = dmc.Group(
        [
            DashIconify(
                icon="carbon:activity",
                width=20,
            ),
            dmc.Text("NEWS and vitals"),
        ]
    )
    panel = dmc.Grid(
        [
            dmc.Col(
                [
                    pred_text,
                    pred_content,
                    news_text,
                    news_content,
                ],
                span=12,
            ),
        ]
    )

    return dmc.AccordionControl(control), dmc.AccordionPanel(panel)


@callback(
    Output(ids.ACC_BED_DECISION_TEXT, "children"),
    Input(ids.ACC_BED_STATUS_CAMPUS, "value"),
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
        Output(ids.ACC_BED_SUBMIT_CAMPUS_NOTIFY, "children"),
        Output(ids.ACC_BED_SUBMIT_CAMPUS, "disabled"),
        Output(ids.ACC_BED_SUBMIT_STORE, "data"),
    ],
    Input(ids.ACC_BED_SUBMIT_CAMPUS, "n_clicks"),
    Input(ids.ACC_BED_STATUS_CAMPUS, "value"),
    State(ids.ACC_BED_SUBMIT_CAMPUS, "disabled"),
    State(ids.CYTO_CAMPUS, "tapNode"),
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

    if callback_context.triggered_id == ids.ACC_BED_STATUS_CAMPUS:
        bed_status_control_value = data.get("dc_status", "").upper()
        disabled = True if bed_status_control_value == status else False
        show = False
    elif callback_context.triggered_id == ids.ACC_BED_SUBMIT_CAMPUS:
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
    Input(ids.CYTO_CAMPUS, "tapNode"),
)
def patient_accordion_item(
    node: dict,
) -> Tuple[dmc.AccordionControl, dmc.AccordionPanel]:
    """Prepare content for bed accordion item"""
    if not node:
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
            sex_icon = (
                "carbon:gender-male" if sex.lower() == "m" else "carbon:gender-female"
            )
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

    try:
        hospital_admit = census.get("hv_admission_dt")
        hospital_los = int((datetime.utcnow() - hospital_admit).days)
        text_los = (
            f"Day {hospital_los}"
            f"(Hospital admission: {datetime.strftime(hospital_admit, '%d %b %Y')})"
        )

    except TypeError:
        text_los = "Hospital length of stay unknown"

    panel = dmc.Group([dmc.Text(text_los)])

    return dmc.AccordionControl(control), dmc.AccordionPanel(panel)


@callback(
    Output(ids.ACCORDION_ITEM_DEBUG, "children"),
    Input(ids.CYTO_CAMPUS, "tapNode"),
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
