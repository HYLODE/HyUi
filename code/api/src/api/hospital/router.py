from fastapi import APIRouter

from api.hospital.wards import tower, gwb, wms, nhnn

router = APIRouter(
    prefix="/hospital",
)


@router.get("/wards")
def get_wards() -> dict[str, list[str]]:
    return {"tower": tower, "gwb": gwb, "wms": wms, "nhnn": nhnn}
