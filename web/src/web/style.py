from pydantic import BaseModel


class AppColors(BaseModel):
    # via http://clrs.cc
    # /* Colors */
    navy: str = "#001F3F"
    blue: str = "#0074D9"
    aqua: str = "#7FDBFF"
    teal: str = "#39CCCC"
    indigo: str = "#5c7cfa"  # via dbc.theme.default_colors
    olive: str = "#3D9970"
    olive50: str = "#3D997080"  # last 2 digits 80 approx 50% alpha
    green: str = "#2ECC40"
    lime: str = "#01FF70"
    yellow: str = "#FFDC00"
    orange: str = "#FF851B"
    red: str = "#FF4136"
    fuchsia: str = "#F012BE"
    purple: str = "#B10DC9"
    maroon: str = "#85144B"
    white: str = "#FFFFFF"
    silver: str = "#DDDDDD"
    gray: str = "#AAAAAA"
    black: str = "#111111"


colors = AppColors()


def replace_colors_in_stylesheet(sheet: list[dict]) -> list[dict]:
    """Standardise to default app colours"""
    sheet = sheet.copy()
    colors_dict = colors.dict()
    for style in sheet:
        for k, v in style.get("style", {}).items():
            if "color" in k and v in colors_dict:
                style.get("style", {}).update({k: colors_dict.get(v)})
    return sheet
