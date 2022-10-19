from pydantic import BaseModel


class AppColors(BaseModel):
    # via http://clrs.cc
    # /* Colors */
    navy: str = "#001F3F"
    blue: str = "#0074D9"
    aqua: str = "#7FDBFF"
    teal: str = "#39CCCC"
    olive: str = "#3D9970"
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
