import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
from . import BPID

_summ_col = ("border rounded border-light border-1 p-2",)
_summ_slider_div = "hstack gap-3"
_summ_slider_label = "w-25 text-end"


abacus_row = dbc.Row(
    id=f"{BPID}ward_status",
    children=[
        # Status summary row
        # ==================
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5(
                                    [
                                        "Admissions ",
                                        html.I(
                                            className="fas fa-question-circle",
                                            id="admissions_tip",
                                        ),
                                    ],
                                    className="text-begin",
                                ),
                                dbc.Tooltip(
                                    "Known admissions are those "
                                    "accepted. Unknown admissions are "
                                    "those emergencies anticipated in the "
                                    "course of a normal day. The default "
                                    "is 1 emergency bed",
                                    target="admissions_tip",
                                    placement="right",
                                    className="text-start",
                                ),
                            ]
                        ),
                    ],
                    className="hstack gap-1 p-0",
                ),
                html.Div(
                    [
                        html.P(
                            "Accepted",
                            className=_summ_slider_label,
                        ),
                        dcc.Slider(
                            id=f"{BPID}adm_confirmed",
                            min=0,
                            max=5,
                            step=1,
                            value=0,
                            marks=None,
                            tooltip={
                                "placement": "top",
                                "always_visible": True,
                            },
                            className="w-75",
                        ),
                    ],
                    className=_summ_slider_div + "pb-0",
                ),
                html.Div(
                    [
                        html.P(
                            "Emergency beds",
                            className=_summ_slider_label,
                        ),
                        dcc.Slider(
                            id=f"{BPID}adm_expected",
                            min=0,
                            max=5,
                            step=1,
                            value=1,
                            marks=None,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                            className="w-75",
                        ),
                    ],
                    className=_summ_slider_div + "pt-0",
                ),
            ],
            width=3,
            className=_summ_col,
        ),
        dbc.Col(
            children=[
                html.Div(
                    [
                        html.H5("Ward occupancy", className="text-begin"),
                    ],
                    className="hstack p-0",
                ),
                html.Div(
                    [
                        html.P("Now", className="w-20 text-end"),
                        dcc.Slider(
                            id=f"{BPID}pts_now_slider",
                            min=0,
                            step=1,
                            marks=None,
                            disabled=False,
                            tooltip={
                                "placement": "top",
                                "always_visible": True,
                            },
                            className="w-100",
                        ),
                    ],
                    className=_summ_slider_div + "pb-0",
                ),
                html.Div(
                    [
                        html.P("Next", className="fw-bold w-20 " "text-end"),
                        dcc.RangeSlider(
                            id=f"{BPID}pts_next_slider",
                            step=1,
                            marks=None,
                            allowCross=False,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                            className="w-100",
                        ),
                    ],
                    className=_summ_slider_div + "pt-0",
                ),
            ],
            width=6,
            className=_summ_col,
        ),
        dbc.Col(
            [
                html.Div(
                    [
                        html.H5("Discharges", className=""),
                    ],
                    className="hstack p-0",
                ),
                html.Div(
                    [
                        html.P("Ready", className=_summ_slider_label),
                        dcc.Slider(
                            id=f"{BPID}dcs_ready",
                            min=0,
                            step=1,
                            marks=None,
                            disabled=True,
                            tooltip={
                                "placement": "top",
                                "always_visible": True,
                            },
                            className="w-100",
                        ),
                    ],
                    className=_summ_slider_div + "pb-0",
                ),
                html.Div(
                    [
                        html.P("Confirmed", className=_summ_slider_label),
                        dcc.Slider(
                            id=f"{BPID}dcs_confirmed",
                            min=0,
                            step=1,
                            value=0,
                            marks=None,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                            className="w-100",
                        ),
                    ],
                    className=_summ_slider_div + "pt-0",
                ),
            ],
            width=3,
            className=_summ_col,
        ),
    ],
    className="border rounded bg-light",
)


@callback(
    (
        Output(f"{BPID}pts_now_slider", "value"),
        Output(f"{BPID}pts_now_slider", "max"),
    ),
    Input(f"{BPID}elements", "data"),
    prevent_initial_callback=True,
)
def show_patients_now(elements: dict):
    n = sum([True for e in elements if e.get("data").get("occupied")])
    return n, 35


@callback(
    (
        Output(f"{BPID}pts_next_slider", "min"),
        Output(f"{BPID}pts_next_slider", "value"),
        Output(f"{BPID}pts_next_slider", "max"),
    ),
    Input(f"{BPID}pts_now_slider", "value"),
    Input(f"{BPID}dcs_confirmed", "value"),
    Input(f"{BPID}adm_confirmed", "value"),
    Input(f"{BPID}adm_expected", "value"),
    prevent_initial_callback=True,
)
def show_patients_next(now: int, dcs: int, adm_con: int, adm_exp: int):
    """
    Values to ba passed to the RangeSlider component
    Args:
        now:
        dcs:
        adm_con:
        adm_exp:

    Returns:

    """
    next = now - dcs + adm_con + adm_exp
    next_upper = next + 1
    next_lower = next - 1

    slider_min = next - 5
    slider_max = next + 5

    return 0, [next_lower, next_upper], 35


@callback(
    (
        Output(f"{BPID}dcs_ready", "value"),
        Output(f"{BPID}dcs_ready", "max"),
        Output(f"{BPID}dcs_confirmed", "max"),
    ),
    Input(f"{BPID}elements", "data"),
    prevent_initial_callback=True,
)
def show_dcs_ready(elements: dict):
    n = sum([True for e in elements if e.get("data").get("discharge")])
    n_max = 5 * ((n // 5) + 1)  # multiple of 5 above n
    return n, n_max, n_max


@callback(
    Output(f"{BPID}dcs_confirmed", "value"),
    Input(f"{BPID}dcs_ready", "value"),
    State(f"{BPID}dcs_confirmed", "value"),
    prevent_initial_callback=True,
)
def show_dcs_confirmed(ready: int, confirmed: int):
    """
    Placeholder callback that should query the number of confirmed discharges
    """
    if confirmed is not None:
        return confirmed
    else:
        return 0


@callback(
    Output(f"{BPID}ward_status", "className"),
    Input(f"{BPID}pts_next_slider", "value"),
    Input(f"{BPID}pts_now_slider", "value"),
    State(f"{BPID}ward_status", "className"),
    prevent_initial_callback=True,
)
def show_highlight_occupancy(pts_next: list[int], pts_now: int, info_class: str):
    """ """
    next_lower, next_upper = pts_next
    if next_upper > pts_now:
        color = "danger"
    elif next_upper < pts_now:
        color = "success"
    else:
        color = "info"

    _default = "border rounded border-2 p-2"
    return "border-" + color + " " + _default
