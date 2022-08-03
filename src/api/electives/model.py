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

import pandas as pd
from pydantic import validator
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

    @validator("pod_orc", "LastUpdatedInstant", "most_recent_pod_dt", pre=True)
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


class ElectivesMock(ElectivesBase, table=True):
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


class ElectivesPreassessMock(ElectivesPreassess, table=True):

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


class ElectivesPodMock(ElectivesPod, table=True):
    """
    This class describes an electives clarity base.
    Post-op destination (pod) from clarity
    """

    id: Optional[int] = Field(default=None, primary_key=True)
