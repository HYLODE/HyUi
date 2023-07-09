from dash import Input, Output, callback

from loguru import logger
from typing import Any
from web import ids as store_ids
from web import SITREP_DEPT2WARD_MAPPING
from web.pages.sitrep import ids


@callback(
    Output(ids.HYMIND_DC_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(store_ids.HYMIND_ICU_DC_STORE, "data"),
)
def _store_hymind_dc(dept: str, hymind_dcs: dict) -> Any:
    """
    Args:
        dept: the department
        hymind_dcs: dictionary of hymind predictions per unit

    Returns:
        additonal individual level dc predictions for that ward

    """
    ward = SITREP_DEPT2WARD_MAPPING.get(dept)
    if not ward:
        logger.warning(f"No HyMind Discharge predictions available for {ward}")
        return [{}]
    return hymind_dcs[ward]
