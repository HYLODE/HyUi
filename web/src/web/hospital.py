import requests

from models.hosptial import BuildingDepartments
from web.config import get_settings


def get_building_departments() -> list[BuildingDepartments]:
    response = requests.get(f"{get_settings().api_url}/hospital/building/departments")
    return [BuildingDepartments.parse_obj(row) for row in response.json()]
