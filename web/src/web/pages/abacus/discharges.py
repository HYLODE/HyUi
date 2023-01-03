"""
Module to manage the CRUD of discharge status
"""
import pytz
import requests
import dash_bootstrap_components as dbc
import dash
from dash import Input, Output, State, callback, ctx, html, dcc
from datetime import datetime
from pydantic import BaseModel

from models.beds import DischargeStatus
from web.config import get_settings
from web.convert import parse_to_data_frame
from web.pages.abacus.map import state_tapnode, input_tapnode
from . import BPID

radio_discharge = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}discharge_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Not ready", "value": "no"},
                        {"label": "End of life", "value": "dying"},
                        {"label": "Review", "value": "review"},
                        {"label": "Ready", "value": "ready"},
                    ],
                    # value="no",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)


form_discharge = html.Div(
    [
        radio_discharge,
        html.Div(
            [
                dbc.Button(
                    "Submit",
                    id=f"{BPID}discharge_submit_button",
                    className="dbc d-grid d-md-flex justify-content-md-end "
                    "btn-group",
                    size="sm",
                    color="primary",
                    disabled=True,
                ),
            ],
            className="dbc d-grid d-md-flex justify-content-md-end",
        ),
    ]
)


store_discharges = dcc.Store(id=f"{BPID}discharge_statuses")
# input_discharges = Input(f"{BPID}discharge_statuses", "data")


def _get_discharge_updates(delta_hours=48):
    response = requests.get(
        f"{get_settings().api_url}/beds/discharge_status",
        params={"delta_hours": delta_hours},
    )
    return response.json()


def _post_discharge_status(csn: int, status: str) -> DischargeStatus:
    response = requests.post(
        url=f"{get_settings().api_url}/beds/discharge_status",
        params={"csn": csn, "status": status},
    )
    return DischargeStatus.parse_obj(response.json())


def _most_recent_row_only(
    rows: list[dict], groupby_col: str, timestamp_col: str, data_model: BaseModel
):
    df = parse_to_data_frame(rows, data_model)
    # remove duplicates here
    df = df.sort_values(timestamp_col, ascending=False)
    df = df.groupby(groupby_col).head(1)
    return df.to_dict(orient="records")


@callback(
    Output(f"{BPID}discharge_statuses", "data"),
    Input(f"{BPID}page_interval", "n_intervals"),
    Input(f"{BPID}discharge_submit_button", "n_clicks"),
    State(f"{BPID}discharge_statuses", "data"),
    State(f"{BPID}discharge_radio", "value"),
    state_tapnode,
    background=True,
)
def store_discharge_statuses(
    n_intervals: int,
    n_clicks: int,
    dc_statuses: list[dict],
    dc_radio: str,
    node: dict,
) -> list[dict]:
    if ctx.triggered_id == f"{BPID}discharge_submit_button":
        all_updates = dc_statuses
        all_updates.append(
            dict(
                csn=node.get("data").get("encounter"),
                status=dc_radio,
                modified_at=datetime.now(tz=pytz.UTC).isoformat(),
            )
        )
    else:
        all_updates = _get_discharge_updates()
    return _most_recent_row_only(
        all_updates,
        groupby_col="csn",
        timestamp_col="modified_at",
        data_model=DischargeStatus,  # noqa
    )


@callback(
    Output(f"{BPID}discharge_radio", "value"),
    input_tapnode,
    prevent_initial_call=True,
)
def set_discharge_radio(node: dict):
    """sets discharge status"""
    if not node:
        return dash.no_update

    status = None
    if any(node) and node.get("data").get("dc_status"):
        status = node.get("data").get("dc_status").get("status")
        status = status if status else "no"
    return status


@callback(
    (
        Output(f"{BPID}discharge_submit_button", "disabled"),
        Output(f"{BPID}discharge_submit_button", "color"),
    ),
    Input(f"{BPID}discharge_submit_button", "n_clicks"),
    Input(f"{BPID}discharge_radio", "value"),
    input_tapnode,
    prevent_initial_call=True,
)
def submit_discharge_status(
    n_clicks: int,
    radio_status: str,
    node: dict,
) -> tuple[bool, str]:
    """
    Submit discharge status button
    Function has two roles
    1. submit using requests.post
    2. manage the colour and enable/disable status of the submit button
    """
    if not node:
        return dash.no_update
    if any(node):
        node_status = node.get("data", {}).get("dc_status", {}).get("status", None)
    else:
        node_status = None
    btn_disabled = True if radio_status == node_status else False
    btn_color = "primary"

    if ctx.triggered_id == f"{BPID}discharge_submit_button":
        encounter = node.get("data").get("encounter")
        res = _post_discharge_status(encounter, radio_status)
        saved_ok = True if res.dict().get("id") else False
        if saved_ok:
            btn_disabled = True
            btn_color = "success"
        else:
            # TODO: display some sort of alert as flash message
            btn_disabled = True
            btn_color = "warning"

    return btn_disabled, btn_color
