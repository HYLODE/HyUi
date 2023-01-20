from fastapi import APIRouter, Depends

from api import wards
from api.dependencies import add_cache_control_header

from models.hospital import BuildingDepartments

router = APIRouter(prefix="/hospital", dependencies=[Depends(add_cache_control_header)])

mock_router = APIRouter(
    prefix="/hospital", dependencies=[Depends(add_cache_control_header)]
)


def _building_departments() -> list[BuildingDepartments]:
    return [
        BuildingDepartments(building="tower", departments=wards.TOWER),
        BuildingDepartments(building="gwb", departments=wards.GWB),
        BuildingDepartments(building="wms", departments=wards.WMS),
        BuildingDepartments(building="nhnn", departments=wards.NHNN),
    ]


@router.get("/building/departments", response_model=list[BuildingDepartments])
def get_building_departments() -> list[BuildingDepartments]:
    return _building_departments()


@mock_router.get("/building/departments", response_model=list[BuildingDepartments])
def get_mock_building_departments() -> list[BuildingDepartments]:
    return _building_departments()
