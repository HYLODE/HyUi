import requests

from models.census import CensusDepartment, ClosedBed
from web.config import get_settings
from web.convert import to_data_frame


def _get_closed_beds() -> list[ClosedBed]:
    response = requests.get(f"{get_settings().api_url}/census/beds/closed/")
    return [ClosedBed.parse_obj(row) for row in response.json()]


def _get_department_census() -> list[CensusDepartment]:
    response = requests.get(f"{get_settings().api_url}/census/departments/")
    return [CensusDepartment.parse_obj(row) for row in response.json()]


def fetch_department_census():
    """
    Stores data from census api (i.e. skeleton)
    Also reaches out to bed_bones and pulls in additional closed beds
    """
    departments = _get_department_census()
    departments_df = to_data_frame(departments, CensusDepartment)

    # Now update with closed beds from bed_bones
    closed_beds = _get_closed_beds()
    closed_beds_df = to_data_frame(closed_beds, ClosedBed)

    closed = closed_beds_df.groupby("department")["closed"].sum()
    departments_df = departments_df.merge(closed, on="department", how="left")
    departments_df["closed"].fillna(0, inplace=True)

    # Then update empties
    departments_df["empties"] = departments_df["empties"] - departments_df["closed"]

    return departments_df[
        [
            "department",
            "beds",
            "patients",
            "empties",
            "days_since_last_dc",
            "closed_temp",
            "closed_perm",
            "modified_at",
            "closed",
        ]
    ].to_dict(orient="records")
