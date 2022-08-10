# src/api/beds/model.py
"""
Beds and current census for wards in the tower flow report

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import date, datetime
from typing import Optional

import arrow
import pandas as pd
from pydantic import validator
from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class BedsBase(SQLModel):
    """
    Consults class to hold data returned from
    the SQL query or the API
    This particular example holds list of patients in the ED
    with pending inpatient consults
    """

    modified_at: datetime
    location_id: int
    department: Optional[str]
    location_string: str

    ovl_admission: Optional[datetime]
    ovl_hv_id: Optional[int]
    open_visits_n: Optional[int]

    cvl_admission: Optional[datetime]
    cvl_discharge: Optional[datetime]
    cvl_hv_id: Optional[int]

    ovl_ghost: Optional[bool]
    occupied: Optional[bool]

    patient_class: Optional[str]

    mrn: Optional[str]
    encounter: Optional[int]
    date_of_birth: Optional[date]
    lastname: Optional[str]
    firstname: Optional[str]
    sex: Optional[str]

    planned_move: Optional[str]
    pm_datetime: Optional[datetime]
    pm_type: Optional[str]
    pm_dept: Optional[str]
    pm_location_string: Optional[str]

    @validator("date_of_birth", pre=True)
    def convert_datetime_to_date(cls, v):
        if isinstance(v, str):
            try:
                return arrow.get(v).date()
            except Exception as e:
                print("Unable to convert date_of_birth to date")
                print(e)
        return v

    # # TODO: how to share functions between classes?
    @validator("ovl_hv_id", "open_visits_n", "cvl_hv_id", "encounter", pre=True)
    def replace_NaN_with_None(cls, v):
        """
        https://stackoverflow.com/questions/47333227/pandas-valueerror-cannot-convert-float-nan-to-integer
        """
        # import pdb; pdb.set_trace()
        # print(v)
        # print(type(v))
        # return v if not np.isnan(v) else None
        return v if not pd.isna(v) else None

    # TODO: how to share functions between classes?
    @validator(
        "ovl_admission",
        "cvl_discharge",
        "cvl_admission",
        "date_of_birth",
        "pm_datetime",
        pre=True,
    )
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        ```
        dfTest = pd.DataFrame(
            [-9223372036854775808, 1655651820000000000],
            columns=['ts']
            )
        dfTest.apply(pd.to_datetime)
        ```
        """
        if any([v is pd.NaT, pd.isna(v)]):
            return None
        else:
            return v


class BedsMock(BedsBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    if "postgres" in settings.STAR_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    beds_id: Optional[int] = Field(default=None, primary_key=True)


class BedsRead(BedsBase):
    """
    Read version that includes the key column
    """

    beds_id: Optional[int]


class BedsDepartments(SQLModel):
    """
    No base version since this will not exist as a database table
    """

    department: str
    beds: int
    patients: int
    empties: int
    opens: int
    last_dc: int
    closed_temp: bool
    modified_at: datetime
