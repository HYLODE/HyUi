"""
Results from Electives Query
eg.

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import date, datetime
from typing import Optional

import pandas as pd
from pydantic import validator, BaseModel
from sqlmodel import Field, SQLModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class ElectiveRow(BaseModel):
    patient_durable_key: str
    surgical_case_epic_id: int
    canceled: bool
    surgical_service: str | None

    class Config:
        alias_generator = _to_camel


class ElectivePostOpDestinationRow(BaseModel):
    pod_orc: str
    or_case_id: int


class ElectivePreassessRow(BaseModel):
    patient_durable_key: str
    name: str
    creation_instant: datetime
    string_value: str

    class Config:
        alias_generator = _to_camel


class GetElectiveRow(BaseModel):
    patient_durable_key: str
    surgical_case_epic_id: int
    canceled: bool
    surgical_service: str | None
    most_recent_pod_dt: str | None
    pod_preassessment: str | None
    most_recent_asa: str | None
    most_recent_mets: str | None
    pod_orc: str | None
    or_case_id: str | None
    pacu: bool


# define the data model that you're expecting from your query
class ElectivesBase(SQLModel):
    """
    Electives class to hold data returned from
    the SQL query or the API
    This particular example holds the results for elective surgical cases
    """

    PrimaryMrn: str
    PatientKey: int
    SurgicalCaseEpicId: int  # use this to join to clarity
    PatientDurableKey: int  # use this to join to caboodle pre-assessment key
    FirstName: str
    LastName: str
    Sex: str
    BirthDate: date
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
    # PostOperativeDestination: Optional[str]
    Name: Optional[str]
    PatientFriendlyName: Optional[str]
    RoomName: Optional[str]
    DepartmentName: Optional[str]
    # preassessment clinic post op destination info
    most_recent_pod_dt: Optional[datetime]
    pod_preassessment: Optional[str]
    most_recent_ASA: Optional[float]
    most_recent_METs: Optional[str]
    # clarity postop destination
    pod_orc: Optional[str]
    SurgeryDateClarity: Optional[datetime]
    pacu: Optional[bool]

    @validator("pod_orc", "pod_preassessment", "most_recent_METs", pre=True)
    def replace_NaN_with_None(cls, v):
        """
        https://stackoverflow.com/questions/47333227/pandas-valueerror-cannot-convert-float-nan-to-integer
        """
        return v if not pd.isna(v) else None

    @validator(
        "SurgeryDateClarity", "LastUpdatedInstant", "most_recent_pod_dt", pre=True
    )
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        """
        if any([v is pd.NaT, pd.isna(v)]):
            return None
        else:
            return v


class ElectivesMock(ElectivesBase, table=True):  # type: ignore
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


class ElectivesPreassess(SQLModel):
    """
    This class describes an electives preassess. Post operative destination
    information derived from pre-assessment clinic smart data elements

    SQL details

    PatientDurableKey   BIGINT  YES NULL
    CreationInstant DATETIME    YES NULL
    StringValue TEXT    YES NULL
    NumericValue    FLOAT   YES NULL
    Name    TEXT    YES NULL
    DataType    TEXT    YES NULL
    """

    PatientDurableKey: int
    CreationInstant: datetime
    StringValue: Optional[str]
    NumericValue: Optional[float]
    Name: Optional[str]
    DataType: Optional[str]

    @validator("StringValue", "Name", "DataType", pre=True)
    def replace_NaN_with_None(cls, v):
        """
        https://stackoverflow.com/questions/47333227/pandas-valueerror-cannot-convert-float-nan-to-integer
        """
        return v if not pd.isna(v) else None

    @validator("CreationInstant", pre=True)
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        """
        if any([v is pd.NaT, pd.isna(v)]):
            return None
        else:
            return v


class ElectivesPreassessMock(ElectivesPreassess, table=True):  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)


# TODO: mocking
class ElectivesPod(SQLModel):
    """
    This class describes an electives clarity base.
    Post-op destination (pod) from clarity
    """

    pod_orc: str
    or_case_id: int
    SurgeryDateClarity: datetime

    @validator("pod_orc", pre=True)
    def replace_NaN_with_None(cls, v):
        """
        https://stackoverflow.com/questions/47333227/pandas-valueerror-cannot-convert-float-nan-to-integer
        """
        return v if not pd.isna(v) else None

    @validator("SurgeryDateClarity", pre=True)
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        """
        if any([v is pd.NaT, pd.isna(v)]):
            return None
        else:
            return v


class ElectivesPodMock(ElectivesPod, table=True):  # type: ignore
    """
    This class describes an electives clarity base.
    Post-op destination (pod) from clarity
    """

    id: Optional[int] = Field(default=None, primary_key=True)
