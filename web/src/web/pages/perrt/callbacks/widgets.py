from dash import Input, Output, callback

from web.pages.perrt import ids
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
    news = [i.get("news_max", -1) for i in beds if i.get("occupied")]
    news_miss = len([i for i in news if i == -1])
    news_low = len([i for i in news if 0 <= i <= 4])
    news_medium = len([i for i in news if 5 <= i <= 6])
    news_high = len([i for i in news if i >= 7])
    empty = N - occupied - blocked

    # Adjust colors and labels based on size
    def _make_progress_label(val: int, N: int, label: str) -> str:
        if val == 0:
            return ""
        elif val / N < 0.2:
            return f"{val}"
        else:
            return f"{val} {label}"

    empty_label = _make_progress_label(empty, N, "empty")
    news_miss_label = _make_progress_label(news_miss, N, "unrecorded")
    news_low_label = _make_progress_label(news_low, N, "Low risk")
    news_medium_label = _make_progress_label(news_medium, N, "Medium risk")
    news_high_label = _make_progress_label(news_high, N, "High risk")
    empty_colour = colors.silver

    return [
        dict(
            value=news_low / N * 100,
            color=colors.olive,
            label=news_low_label,
            tooltip=f"{news_low} low risk patients",
        ),
        dict(
            value=news_miss / N * 100,
            color=colors.indigo,
            label=news_miss_label,
            tooltip=f"{news_miss} patients without recent NEWS",
        ),
        dict(
            value=news_medium / N * 100,
            color="#F5C487",
            label=news_medium_label,
            tooltip=f"{news_medium} medium risk patients",
        ),
        dict(
            value=news_high / N * 100,
            color="#EC9078",
            label=news_high_label,
            tooltip=f"{news_high} high risk patients",
        ),
        dict(
            value=empty / N * 100,
            color=empty_colour,
            label=empty_label,
            tooltip=f"{empty} empty beds",
        ),
    ]


@callback(
    Output(ids.PROGRESS_CAMPUS, "sections"),
    Input(ids.CYTO_CAMPUS, "elements"),
    prevent_initial_call=True,
)
def progress_bar_campus(elements: list[dict]) -> list[dict]:
    return _progress_bar_bed_count(elements)
