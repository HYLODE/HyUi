"""
Module to manage the department menus
Exposes
- dcc.Store of list of departments
- dash.Input holding the currently selected department
- radio_campus
- dept_dropdown

"""

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

from web.hospital import get_building_departments
from . import BPID, SITREP_DEPT2WARD_MAPPING

store_dept_list = dcc.Store(id=f"{BPID}departments")
store_active_dept = dcc.Store(id=f"{BPID}active_dept")
input_active_dept = Input(f"{BPID}active_dept", "data")

radio_icu = html.Div(
    [
        html.Div(
            [
                dbc.RadioItems(
                    id=f"{BPID}icu_radio",
                    className="dbc d-grid d-md-flex justify-content-md-begin "
                    "btn-group p-1",
                    inline=True,
                    options=[
                        {"label": v, "value": k}
                        for k, v in SITREP_DEPT2WARD_MAPPING.items()
                    ]
                    + [{"label": "Other", "value": "other"}],
                    value="UCH T03 INTENSIVE CARE",
                )
            ],
            className="dbc",
        ),
    ],
    className="radio-group",
)

dropdown_dept = html.Div(
    [
        dcc.Dropdown(
            id=f"{BPID}dept_dropdown",
            placeholder="Select 'Other' to choose other wards",
            multi=False,
            className="p-0",
        )
    ],
    className="dbc",
)


@callback(
    Output(f"{BPID}departments", "data"),
    Input(f"{BPID}page_interval", "n_intervals"),
    background=True,
)
def _store_all_departments(_: int) -> list[dict]:
    """
    Store a list of departments for the building
    Triggers the update of most of the elements on the page
    """
    building_departments = get_building_departments()
    return [bd.dict() for bd in building_departments]


@callback(
    (
        Output(f"{BPID}dept_dropdown", "options"),
        Output(f"{BPID}dept_dropdown", "disabled"),
        Output(f"{BPID}dept_dropdown", "value"),
    ),
    Input(f"{BPID}icu_radio", "value"),
    Input(f"{BPID}departments", "data"),
)
def _gen_dept_dropdown(
    icu_radio: str, building_departments: list
) -> tuple[list[dict], bool, str]:
    """
    Dynamically build department picker list
    """

    dropdown: list[str] = []
    for bd in building_departments:
        dropdown.extend(bd.get("departments"))
    options = [{"label": v, "value": v, "search": v} for v in dropdown]

    if icu_radio == "other":
        return options, False, ""
    else:
        return options, True, ""


@callback(
    Output(f"{BPID}active_dept", "data"),
    Input(f"{BPID}icu_radio", "value"),
    Input(f"{BPID}dept_dropdown", "value"),
)
def _store_active_department(icu: str, dept: str) -> str:
    if icu != "other":
        return icu
    else:
        return dept
