import dash
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import dcc, html


from web.logger import logger
from web.pages.ed import ids

from web.pages.ed import callbacks  # noqa


dash.register_page(__name__, path="/ed/table", name="ED")


logger.debug("Confirm that you have imported all the callbacks")

grid = dag.AgGrid(
    id=ids.PATIENTS_GRID,
    columnSize="responsiveSizeToFit",
    defaultColDef={
        # "autoSize": True,
        "resizable": True,
        "sortable": True,
        "filter": True,
        # "minWidth": 100,
        # "responsiveSizeToFit": True,
        # "columnSize": "sizeToFit",
    },
    className="ag-theme-material",
)

stores = html.Div(
    [
        dcc.Store(id=ids.PATIENTS_STORE),
        dcc.Store(id=ids.AGGREGATE_STORE),
    ]
)
notifications = html.Div(
    [
        # html.Div(id=ids.ACC_BED_SUBMIT_WARD_NOTIFY),
    ]
)

body = dmc.Container(
    [
        dmc.Grid(
            children=[
                # dmc.Col(progress, span=12),
                dmc.Col(grid, span=12),
            ],
        ),
    ],
    style={"width": "100vw"},
    fluid=True,
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            stores,
            notifications,
            body,
            # inspector,
        ]
    )
