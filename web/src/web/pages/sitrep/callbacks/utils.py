import dash_mantine_components as dmc
import warnings
from typing import Tuple


def _resp_organ_status(status: str) -> Tuple[str, str]:
    status = status.lower()
    if status == "ventilated":
        label, color = "Ventilated", "red"
    elif status in ["hfno", "cpap", "niv"]:
        label, color = status, "orange"
    elif status in ["oxygen"]:
        label, color = "O2", "yellow"
    elif status in ["room air"]:
        label, color = "No resp support", "green"
    else:
        label, color = "? resp support", "gray"
    label = label.upper()
    return label, color


def _cvs_organ_status(status: int) -> Tuple[str, str]:
    if status >= 2:
        label, color = "2+ vasoactive", "red"
    elif status == 1:
        label, color = "1 vasoactive", "orange"
    elif status == 0:
        label, color = "0 vasoactive", "green"
    else:
        raise ValueError(f"{status} not a recognised count of vasoactives")
    return label, color


def _renal_organ_status(status: bool) -> Tuple[str, str]:
    if status is True:
        label, color = "RRT", "red"
    elif status is None:
        label, color = "? renal support", "gray"
    elif status is False:
        label, color = "No RRT", "green"
    else:
        raise ValueError(f"{status} not a recognised RRT status")
    return label, color


def _delirium_status(status: bool) -> Tuple[str, str]:
    if status is True:
        label, color = "Agitated", "red"
    elif status is None:
        label, color = "Delirium unreported", "gray"
    elif status is False:
        label, color = "No delirium", "green"
    else:
        raise ValueError(f"{status} not a recognised agitation status")
    return label, color


def make_sitrep_badge(organ: str, sitrep: dict) -> dmc.Badge:
    if organ == "vent_type_1_4h":
        value, color = _resp_organ_status(sitrep.get(organ, ""))
    elif organ == "n_inotropes_1_4h":
        value, color = _cvs_organ_status(sitrep.get(organ, 0))
    elif organ == "had_rrt_1_4h":
        value, color = _renal_organ_status(sitrep.get(organ, None))
    elif organ == "is_agitated_1_8h":
        value, color = _delirium_status(sitrep.get(organ, None))
    else:
        warnings.warn(f"{organ} not recognised to create sitrep badge")
        value, color = "Unknown", "gray"

    return dmc.Badge(value, color=color, variant="filled")
