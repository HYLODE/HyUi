from pydantic import BaseModel


class BuildingDepartments(BaseModel):
    building: str
    departments: list[str]
