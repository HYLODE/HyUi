# src/api/electives/model.py
"""
Results from Electives Query
eg.

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


# define the data model that you're expecting from your query
class ElectivesBase(SQLModel):
    """
    Electives class to hold data returned from
    the SQL query or the API
    This particular example holds the results for elective surgical cases
    """

    PrimaryMrn: str
    PatientKey: int
    PatientDurableKey: int
    AgeInYears: int
    PlacedOnWaitingListDate: Optional[date]
    DecidedToAdmitDate: Optional[date]
    AdmissionService: Optional[str]
    ElectiveAdmissionType: Optional[str]
    IntendedManagement: Optional[str]
    Priority: Optional[str]
    RemovalReason: Optional[str]
    Status: Optional[str]
    Subgroup: Optional[str]
    SurgicalService: Optional[str]
    Type: Optional[str]
    LastUpdatedInstant: Optional[datetime]
    SurgeryDate: Optional[date]
    PrimaryService: Optional[str]
    Classification: Optional[str]
    SurgeryPatientClass: Optional[str]
    AdmissionPatientClass: Optional[str]
    PrimaryAnesthesiaType: Optional[str]
    ReasonNotPerformed: Optional[str]
    Canceled: Optional[int]
    SurgicalCaseUclhKey: int
    SurgicalCaseKey: int
    CaseScheduleStatus: Optional[str]
    CaseCancelReason: Optional[str]
    CaseCancelReasonCode: Optional[str]
    CancelDate: Optional[date]
    PlannedOperationStartInstant: datetime
    PlannedOperationEndInstant: datetime
    PostOperativeDestination: Optional[str]
    Name: Optional[str]
    PatientFriendlyName: Optional[str]
    RoomName: Optional[str]
    DepartmentName: Optional[str]


class Electives(ElectivesBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    id: Optional[int] = Field(default=None, primary_key=True)


class ElectivesRead(ElectivesBase):
    """
    Read version that includes the key column
    """

    id: Optional[int]
