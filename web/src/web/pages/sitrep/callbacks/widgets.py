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
    discharges = len([i for i in beds if i.get("dc_status") == "discharge"])
    reviews = len([i for i in beds if i.get("dc_status") == "review"])
    exits = len([i for i in beds if i.get("dc_status") in ["excellence"]])
    holding = occupied - discharges - reviews - exits
    empty = N - occupied - blocked
    empty_p = empty / N

    # Adjust colors and labels based on size
    def _make_progress_label(val: int, N: int, label: str) -> str:
        if val == 0:
            return ""
        elif val / N < 0.2:
            return f"{val}"
        else:
            return f"{val} {label}"

    blocked_label = _make_progress_label(blocked, N, "blocked")
    empty_label = _make_progress_label(empty, N, "empty")
    holding_label = _make_progress_label(holding, N, "residing")
    discharges_label = _make_progress_label(discharges, N, "discharges")
    reviews_label = _make_progress_label(reviews, N, "reviews")
    exits_label = _make_progress_label(exits, N, "EoL")

    if empty_p < 0.05:
        empty_colour = colors.red
    elif empty_p < 0.1:
        empty_colour = colors.yellow
    else:
        empty_colour = colors.silver

    return [
        dict(
            value=holding / N * 100,
            color=colors.indigo,
            label=holding_label,
            tooltip=f"{holding} beds",
        ),
        dict(
            value=reviews / N * 100,
            color=colors.teal,
            label=reviews_label,
            tooltip=f"{reviews} beds",
        ),
        dict(
            value=exits / N * 100,
            color=colors.black,
            label=exits_label,
            tooltip=f"{exits} beds",
        ),
        dict(
            value=discharges / N * 100,
            color=colors.olive,
            label=discharges_label,
            tooltip=f"{discharges} beds",
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
