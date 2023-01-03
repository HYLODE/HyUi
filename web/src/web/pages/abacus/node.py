"""
Module to manage the display of patient details on the page
Exposes
- node_title: html element with formatted title
- node_details: html element with formatted details
- node_debug: html element with unformatted text for debugging
"""
import dash_bootstrap_components as dbc
import json
from dash import Output, callback, html
from datetime import datetime

from web import icons
from web.pages.abacus.discharges import form_discharge
from web.pages.abacus.map import input_tapnode, input_selected_nodes
from . import BPID

styles = {"debug": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

node_debug = html.Pre(id=f"{BPID}node_debug", style=styles["debug"])
_header = html.Div(id=f"{BPID}node_header")
_body = html.Div(id=f"{BPID}node_body")

card_node = html.Div(
    id=f"{BPID}card_visible",
    children=dbc.Card(
        [
            dbc.CardHeader(_header),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            _body,
                            form_discharge,
                        ],
                        id=f"{BPID}card_body_visible",
                    ),
                ]
            ),
        ]
    ),
)


@callback(
    Output(f"{BPID}node_debug", "children"),
    input_tapnode,
    prevent_initial_callback=True,
)
def tap_debug_inspector(data: dict):
    return json.dumps(data, indent=4)


@callback(
    Output(f"{BPID}card_visible", "hidden"),
    input_selected_nodes,
    input_tapnode,
    prevent_initial_callback=True,
)
def set_card_visible(nodes: list[dict], tap_node: dict):
    """set the hidden property of the card_visible div"""

    if not nodes or not len(nodes):
        return True

    node = tap_node.get("data")
    if node.get("level") != "bed":
        return True

    return False


@callback(
    Output(f"{BPID}card_body_visible", "hidden"),
    input_selected_nodes,
    input_tapnode,
    prevent_initial_callback=True,
)
def set_card_body_visible(nodes: list[dict], tap_node: dict):
    """set the hidden property of the card_visible div"""

    if not nodes or not len(nodes):
        return True

    node = tap_node.get("data")
    if node.get("level") == "room":
        return True
    if node.get("occupied", False) is False:
        return True
    return False


@callback(
    Output(f"{BPID}node_header", "children"),
    input_tapnode,
    prevent_initial_callback=True,
)
def _node_title(node: dict):
    """
    Prettify node
    """
    if node is None:
        return ""
    if node.get("data").get("level") != "bed":
        return ""

    node_data = node.get("data")
    census = node_data.get("census")

    bed_label = node_data.get("bed_index")
    bed_title = html.H5(f"Bed {bed_label}")

    if not node_data.get("occupied"):
        return bed_title

    sitrep = node_data.get("sitrep")

    mrn = census.get("mrn", "")
    encounter = str(census.get("encounter", ""))
    lastname = census.get("lastname", "").upper()
    firstname = census.get("firstname", "").title()
    date_of_birth = census.get("date_of_birth")
    age = int((datetime.utcnow() - datetime.fromisoformat(date_of_birth)).days / 365.25)
    sex = census.get("sex")
    if sex is None:
        sex = ""
    else:
        sex = "M" if sex.lower() == "m" else "F"

    pt_title = html.H5(
        f"{firstname} {lastname} | {age}{sex} | {mrn}", className="fw-bold"
    )

    organ_support = html.H5(_organ_icons(sitrep)) if sitrep else html.H5("")

    return html.Div(
        [bed_title, pt_title, organ_support],
        className="hstack gap-3 justify-content-between",
    )


def _organ_icons(sitrep: dict) -> object:
    rs = sitrep.get("vent_type_1_4h")
    rs_icon = icons.rs_dbc(rs)

    aki = sitrep.get("had_rrt_1_4h")
    aki_icon = icons.aki_dbc(aki)

    cvs = sitrep.get("n_inotropes_1_4h")
    cvs_icon = icons.cvs_dbc(cvs)

    return [
        html.I(className=rs_icon),
        " ",
        html.I(className=cvs_icon),
        " ",
        html.I(className=aki_icon),
    ]


@callback(
    Output(f"{BPID}node_body", "children"),
    input_tapnode,
    prevent_initial_callback=True,
)
def _node_body(node: dict):
    if node is None:
        return ""
    if node.get("data").get("level") != "bed":
        return ""

    node_data = node.get("data")

    census = node_data.get("census")
    if node_data.get("occupied"):
        mrn = html.Tr([html.Td("MRN"), html.Td(census.get("mrn", ""))])
        encounter = html.Tr([html.Td("CSN"), html.Td(str(census.get("encounter", "")))])
        lastname = html.Tr(
            [html.Td("Last name"), html.Td(census.get("lastname", "").upper())]
        )
        firstname = html.Tr(
            [html.Td("First name"), html.Td(census.get("firstname", "").title())]
        )
        date_of_birth = html.Tr(
            [html.Td("Date of Birth"), html.Td(census.get("date_of_birth"))]
        )

        sex = census.get("sex")
        if sex is None:
            sex = ""
        else:
            sex = "M" if sex.lower() == "m" else "F"
        sex = html.Tr([html.Td("Sex"), html.Td(sex)])

        census_rows = [mrn, lastname, firstname, date_of_birth, sex, encounter]
    else:
        census_rows = []

    sitrep = node_data.get("sitrep")
    if sitrep:
        rs = html.Tr(
            [html.Td("Respiratory Support"), html.Td(sitrep.get("vent_type_1_4h", ""))]
        )
        cvs = html.Tr(
            [
                html.Td("Cardiovascular Support"),
                html.Td(sitrep.get("n_inotropes_1_4h", "")),
            ]
        )
        aki = sitrep.get("had_rrt_1_4h")
        aki_string = "CVVHDF" if aki else "No RRT"
        aki_row = html.Tr([html.Td("Renal Support"), html.Td(aki_string)])
        sitrep_rows = [rs, cvs, aki_row]
    else:
        sitrep_rows = []

    table_header = [html.Thead(html.Tr([html.Th(), html.Th()]))]
    table_body = [html.Tbody(census_rows + sitrep_rows)]

    # return dbc.Table(table_header + table_body, bordered=True)
    return dbc.Table(table_body, bordered=True, size="sm", striped=True)
