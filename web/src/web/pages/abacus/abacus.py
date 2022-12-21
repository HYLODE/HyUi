"""
Layout for sub-application for the abacus endpoint
"""
# TODO: generalise to work with any ward using concentric lay out so strip
#  out sitrep data for now; and store census data on the page

DEBUG = False

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import dcc, html, register_page

if DEBUG:
    from . import BPID
    import abacus.callbacks  # noqa
else:
    import web.pages.abacus.callbacks  # noqa: F401
    from web.pages.abacus import BPID

    register_page(__name__, name="ABACUS")

DEPARTMENT = "UCH T03 INTENSIVE CARE"
DEPARTMENTS = [DEPARTMENT, "GWB L01 CRITICAL CARE"]
REFRESH_INTERVAL = 10 * 60 * 1000  # 10 mins in milliseconds

building_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}building_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Tower", "value": "tower"},
                        {"label": "GWB", "value": "gwb"},
                        {"label": "WMS", "value": "wms"},
                        {"label": "NHNN", "value": "nhnn"},
                    ],
                    value="tower",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

layout_radio_button = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}layout_radio",
                    className="dbc d-grid d-md-flex "
                    "justify-content-md-end btn-group",
                    inline=True,
                    options=[
                        {"label": "Map", "value": "preset"},
                        {"label": "Circle", "value": "circle"},
                        {"label": "Grid", "value": "grid"},
                    ],
                    value="circle",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

dash_only = html.Div(
    [
        dcc.Interval(
            id=f"{BPID}query_interval",
            interval=REFRESH_INTERVAL,
            n_intervals=0,
        ),
        dcc.Store(id=f"{BPID}departments"),
        dcc.Store(id=f"{BPID}census"),
        dcc.Store(id=f"{BPID}beds"),
        dcc.Store(id=f"{BPID}patients_in_beds"),
    ]
)

ward_map = html.Div(
    [
        cyto.Cytoscape(
            id=f"{BPID}bed_map",
            style={
                # "width": "600px",
                # "height": "600px",
                "width": "42vw",
                "height": "80vh",
                "position": "relative",
                "top": "4vh",
                "left": "4vw",
            },
            stylesheet=[
                {"selector": "node", "style": {"label": "data(label)"}},
                {
                    "selector": "[?occupied]",
                    "style": {
                        "shape": "ellipse",
                        # "background-color": "#ff0000",
                        # "background-opacity": 1.0,
                        "border-width": 2,
                        "border-style": "solid",
                        "border-color": "red",
                    },
                },
                {
                    "selector": '[!occupied][level="bed"]',
                    "style": {
                        "shape": "rectangle",
                        "background-color": "grey",
                        "background-opacity": 0.2,
                        "border-width": 2,
                        "border-style": "solid",
                        "border-color": "black",
                    },
                },
                {
                    "selector": '[!visible][level="room"]',
                    "style": {
                        "background-opacity": 0.0,
                        "border-opacity": 0.0,
                    },
                },
            ],
            responsive=True,
            maxZoom=1.0,
            # zoom=1,
            minZoom=0.2,
        )
    ]
)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # html.Div("Row 1 Column 1"),
                            html.Div(id=f"{BPID}dept_title"),
                            # html.Div(id=f"{BPID}ward_map"),
                            ward_map,
                        ],
                        # width={"size": 6, "order": "first", "offset": 6},
                    ),
                    dbc.Col(
                        [
                            # html.Div("Row 1 Column 2"),
                            # html.Button('Reset', id=f"{BPID}reset", n_clicks=0),
                            building_radio_button,
                            layout_radio_button,
                            html.Div(id=f"{BPID}dept_dropdown_div"),
                            # html.Pre(id="bed_inspector", style=styles["pre"]),
                            # html.Pre(id="node_inspector", style=styles[
                            # "pre"]),
                        ],
                        # width={"size": 6, "order": "last", "offset": 6},
                    ),
                ]
            ),
            html.Div(id=f"{BPID}ward_map"),
            dash_only,
        ]
    )


if DEBUG:
    from dash import Dash

    app = Dash(
        __name__,
        # server=server,
        title="HYLODE",
        update_title=None,
        external_stylesheets=[
            dbc.themes.LUX,
            dbc.icons.FONT_AWESOME,
        ],
        suppress_callback_exceptions=True,
        # use_pages=True,
        # background_callback_manager=DiskcacheManager(cache),
    )
    server = app.server

    if __name__ == "__main__":
        app.layout = layout()
        app.run_server(debug=True)
