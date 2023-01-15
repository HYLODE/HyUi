from dash import Input, Output, callback

from web.pages.sitrep import ids
from web.style import colors

DEBUG = True


def _progress_bar_bed_count(elements: list[dict]) -> list[dict]:
    """Given elements from a cytoscape bed map then prepare sections for
    progress bar"""
    beds = [
        ele.get("data", {})
        for ele in elements
        if ele.get("data", {}).get("entity") == "bed"
    ]

    # TODO: replace with total capacity from department sum
    N = len(beds)
    occupied = len([i for i in beds if i.get("occupied")])
    blocked = len([i for i in beds if i.get("blocked")])
    empty = N - occupied - blocked
    empty_p = empty / N

    # Adjust colors and labels based on size
    blocked_label = "" if blocked / N < 0.1 else "Blocked"
    empty_label = "" if empty_p < 0.1 else "Empty"
    if empty_p < 0.05:
        empty_colour = colors.red
    elif empty_p < 0.1:
        empty_colour = colors.yellow
    else:
        empty_colour = colors.silver

    return [
        dict(
            value=occupied / N * 100,
            color=colors.indigo,
            label="Occupied",
            tooltip=f"{occupied} beds",
        ),
        dict(
            value=blocked / N * 100,
            color=colors.gray,
            label=blocked_label,
            tooltip=f"{blocked} beds",
        ),
        dict(
            value=empty / N * 100,
            color=empty_colour,
            label=empty_label,
            tooltip=f"{empty} beds",
        ),
    ]


@callback(
    Output(ids.PROGRESS_CAMPUS, "sections"),
    Input(ids.CYTO_CAMPUS, "elements"),
    prevent_initial_call=True,
)
def progress_bar_campus(elements: list[dict]) -> list[dict]:
    return _progress_bar_bed_count(elements)


@callback(
    Output(ids.PROGRESS_WARD, "sections"),
    Input(ids.CYTO_WARD, "elements"),
    prevent_initial_call=True,
)
def progress_bar_ward(elements: list[dict]) -> list[dict]:
    return _progress_bar_bed_count(elements)
