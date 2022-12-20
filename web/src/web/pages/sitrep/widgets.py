from dash import html
import dash_bootstrap_components as dbc
from web.pages.sitrep import BPID

department_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}ward_radio",
                    className="dbc d-grid d-md-flex justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "T03", "value": "UCH T03 INTENSIVE CARE"},
                        {"label": "T06", "value": "UCH T06 SOUTH PACU"},
                        {"label": "GWB", "value": "GWB L01 CRITICAL CARE"},
                        {"label": "WMS", "value": "WMS W01 CRITICAL CARE"},
                        {"label": "NHNN0", "value": "NHNN C0 NCCU"},
                        {"label": "NHNN1", "value": "NHNN C1 NCCU"},
                    ],
                    value="UCH T03 INTENSIVE CARE",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

closed_beds_switch = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}closed_beds_switch",
                    className="dbc d-grid d-md-flex justify-content-md-end",
                    inline=True,
                    options=[
                        {"label": "Open beds", "value": False},
                        {"label": "All beds", "value": True},
                    ],
                    value=False,
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)
