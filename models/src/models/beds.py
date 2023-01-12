from datetime import datetime
from pydantic import BaseModel


class DischargeStatus(BaseModel):
    id: int | None
    order: float | None
    csn: int
    status: str
    modified_at: datetime


class Bed(BaseModel):
    location_name: str | None
    department: str | None
    room: str | None
    hl7_bed: str | None
    location_string: str | None
    hl7_department: str | None
    hl7_room: str | None
    location_id: int | None
    department_id: int | None
    room_id: int | None
    bed_id: int | None
    bed_number: int | None
    floor: int | None
    bed_index: int | None
    closed: bool | None
    covid: bool | None
    xpos: int | None
    ypos: int | None


class Department(BaseModel):
    department: str | None
    hl7_department: str | None
    department_id: int | None
    floor: int | None
    floor_order: int | None
    closed_perm_01: bool | None
    clinical_service: str | None
    department_external_name: str | None
    department_speciality: str | None
    department_service_grouper: str | None
    department_level_of_care_grouper: str | None
    location_name: str | None


class Room(BaseModel):
    hl7_room: str
    room: str | None
    room_id: int | None
    department: str | None
    is_room: bool | None
    has_beds: bool | None
