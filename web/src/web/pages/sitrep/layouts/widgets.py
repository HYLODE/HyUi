import dash_mantine_components as dmc
from dash import html

from web.pages.sitrep import CAMPUSES, ids

campus_selector = html.Div(
    [
        dmc.SegmentedControl(
            id=ids.DEPT_GROUPER,
            value=[i.get("value") for i in CAMPUSES if i.get("label") == "UCH"][0],
            data=CAMPUSES,
            persistence=True,
            persistence_type="local",
        ),
    ]
)
