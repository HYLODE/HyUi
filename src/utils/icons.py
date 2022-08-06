# src/utils/icons.py
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
    try:
        level = level.lower()
    except AttributeError:
        level = "unknown"

    if level == "false":
        colour = COLOUR_GREY
    elif level == "true":
        colour = COLOUR_RED
    else:
        colour = COLOUR_GREY
    icon_string = f'<i class="{icon}" style="color: {colour};"></i>'
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
