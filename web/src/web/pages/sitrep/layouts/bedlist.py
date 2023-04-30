from dash import Input, Output, callback, html
from types import SimpleNamespace
from typing import Any

from web.pages.sitrep import ids
from web.pages.sitrep.callbacks.census import format_census

DEBUG = True


@callback(Output(ids.BED_SELECTOR_WARD, "children"), Input(ids.CYTO_WARD, "elements"))
def _prep_bed_selector(elements: list[dict]) -> list[Any]:
    header = [
        html.Thead(
            [
                html.Tr(
                    [
                        html.Th(
                            "Bed", style={"text-align": "end", "padding-right": "10px"}
                        ),
                        html.Th("Patient", style={"text-align": "start"}),
                    ]
                )
            ]
        )
    ]

    if not elements:
        return header + []

    data = [
        ele.get("data", {})
        for ele in elements
        if ele.get("data", {}).get("entity") == "bed"
    ]

    rows = []
    for dat in data:
        occupied = dat.get("occupied")
        full_name = ""
        bed_number = dat.get("bed_number", "")
        if occupied:
            census = dat.get("census")
            cfmt = SimpleNamespace(**format_census(census))
            full_name = f"{cfmt.firstname} {cfmt.lastname}"
        row = html.Tr(
            [
                html.Td(
                    bed_number,
                    style={
                        "text-align": "end",
                        "font-weight": "bold",
                        "font-family": "monospace",
                        "padding-right": "10px",
                    },
                ),
                html.Td(full_name, style={"text-align": "start"}),
            ]
        )
        rows.append(row)
    body = [html.Tbody(rows)]

    return header + body
