from datetime import datetime, date

from fastapi import APIRouter

from models.ed import EmergencyDepartmentPatient, AggregateAdmissionRow

router = APIRouter(
    prefix="/ed",
)

mock_router = APIRouter(
    prefix="/ed",
)


@mock_router.get("/individual/", response_model=list[EmergencyDepartmentPatient])
def get_individual_admission_rows():
    return [
        EmergencyDepartmentPatient(
            arrival_datetime=datetime(2022, 10, 12, 13, 14),
            bed="BED1",
            mrn="MRNABC",
            name="Name A",
            sex="F",
            date_of_birth=date(1990, 10, 6),
            admission_probability=0.56,
        )
    ]


@mock_router.get("/aggregate/", response_model=list[AggregateAdmissionRow])
def get_aggregate_admission_rows():
    return [
        AggregateAdmissionRow(
            speciality="medical",
            beds_allocated=5,
            beds_not_allocated=2,
            without_decision_to_admit_seventy_percent=6,
            without_decision_to_admit_ninety_percent=4,
            yet_to_arrive_seventy_percent=10,
            yet_to_arrive_ninety_percent=6,
        )
    ]
