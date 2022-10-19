from fastapi import APIRouter

from api import wards

router = APIRouter(
    prefix="/hospital",
)


@router.get("/wards")
def get_wards() -> dict[str, tuple[str, ...]]:
    return {
        "tower": wards.TOWER,
        "gwb": wards.GWB,
        "wms": wards.WMS,
        "nhnn": wards.NHNN,
    }
