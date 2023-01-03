"""
Functions for icons in dash tables etc
"""

COLOUR_GREY = "#c0c0c077"
COLOUR_GREEN = "#008000ff"
COLOUR_AMBER = "#ffa500ff"
COLOUR_RED = "#ff0000ff"


def covid(value: bool) -> str:
    if value:
        icon = "fa fa-virus-covid"
        colour = COLOUR_RED
    else:
        icon = "fa fa-virus"
        colour = COLOUR_GREY
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
    return icon_string


def closed(value: bool) -> str:
    if value:
        icon = "fa fa-ban"
        colour = COLOUR_RED
    else:
        icon = "fa fa-ban"
        colour = COLOUR_GREY
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
    return icon_string


def aki(level: str) -> str:
    icon = "fa fa-flask"

    if level is False:
        colour = COLOUR_GREY
    elif level is True:
        colour = COLOUR_RED
    else:
        colour = COLOUR_AMBER
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
    return icon_string


def aki_dbc(level: bool) -> str:
    icon = "fa fa-flask"

    if type(level) is not bool:
        colour = "text-dark"
    elif level is False:
        colour = "text-success"
    elif level is True:
        colour = "text-danger"
    else:
        colour = "text-info"

    icon_string = f"{icon} {colour}"
    return icon_string


def rs(level: str) -> str:
    icon = "fa fa-lungs"

    try:
        level = level.lower()
    except AttributeError:
        level = "unknown"

    if level in ["unknown", "room air"]:
        colour = COLOUR_GREY
    elif level in ["oxygen"]:
        colour = COLOUR_GREEN
    elif level in ["hfno", "niv", "cpap"]:
        colour = COLOUR_AMBER
    else:
        colour = COLOUR_RED
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
    return icon_string


def rs_dbc(level: str) -> str:
    """dash bootstrap component version"""
    icon = "fa fa-lungs"

    try:
        level = level.lower()
    except AttributeError:
        level = "unknown"

    if level in ["unknown", "room air"]:
        colour = "text-light"
    elif level in ["oxygen"]:
        colour = "text-success"
    elif level in ["hfno", "niv", "cpap"]:
        colour = "text-warning"
    else:
        colour = "text-danger"
    icon_string = f"{icon} {colour}"
    return icon_string


def cvs(level: str) -> str:
    icon = "fa fa-heart"
    try:
        n = int(level)
    except (ValueError, TypeError):
        n = 0
    if n == 0:
        colour = COLOUR_GREY
    elif n == 1:
        colour = COLOUR_AMBER
    else:
        colour = COLOUR_RED
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
    return icon_string


def cvs_dbc(level: int) -> str:
    icon = "fa fa-heart"

    if type(level) is not int:
        colour = "text-dark"
    elif level == 0:
        colour = "text-success"
    elif level == 1:
        colour = "text-warning"
    elif level > 1:
        colour = "text-danger"
    else:
        colour = "text-info"

    icon_string = f"{icon} {colour}"
    return icon_string
