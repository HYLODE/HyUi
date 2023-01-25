"""
Utility functions to access common endpoints
e.g. list of departments
"""
import requests

from models.hospital import BuildingDepartments
from models.census import CensusBed
from web.config import get_settings


def get_building_departments() -> list[BuildingDepartments]:
    """Request and parse list of buildings and available departments"""
    response = requests.get(f"{get_settings().api_url}/hospital/building/departments")
    return [BuildingDepartments.parse_obj(row) for row in response.json()]


def departments_by_building(building: str) -> list[str]:
    """Filter the departments by building"""
    building_departments = get_building_departments()
    departments: list[str] = []
    for bd in building_departments:
        if bd.building == building:
            departments.extend(bd.departments)
            break
    return departments
