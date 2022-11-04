from fastapi import APIRouter

from api import wards

from models.hosptial import BuildingDepartments

router = APIRouter(
    prefix="/hospital",
)

mock_router = APIRouter(
    prefix="/hospital",
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
