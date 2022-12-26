import requests

from models.census import CensusDepartment, CensusRow
from web.config import get_settings
from web.convert import to_data_frame


# def _get_closed_beds() -> list[Bed]:
#     response = requests.get(f"{get_settings().api_url}/beds/closed/")
#     return [Bed.parse_obj(row) for row in response.json()]


def get_census(departments: list[str], locations: list[str] = None) -> list[CensusRow]:
    response = requests.get(
        url=f"{get_settings().api_url}/census/",
        params={"departments": departments, "locations": locations},
    )
    return [CensusRow.parse_obj(row) for row in response.json()]


def get_department_status() -> list[CensusDepartment]:
    response = requests.get(f"{get_settings().api_url}/census/departments/")
    return [CensusDepartment.parse_obj(row) for row in response.json()]


def fetch_department_census():
    """
    Stores data from census api (i.e. skeleton)
    Also reaches out to beds and pulls in additional closed beds
    """
    departments = get_department_status()
    departments_df = to_data_frame(departments, CensusDepartment)

    # TODO: rebuild to capture the beds reported to be closed in baserow
    # Now update with closed beds from beds
    # closed_beds = _get_closed_beds()
    # closed_beds_df = to_data_frame(closed_beds, ClosedBed)
    #
    # closed = closed_beds_df.groupby("department")["closed"].sum()
    # departments_df = departments_df.merge(closed, on="department", how="left")
    # departments_df["closed"].fillna(0, inplace=True)
    departments_df["closed"] = 0
    departments_df.head()

    # Then update empties
    # departments_df["empties"] = departments_df["empties"] - departments_df[
    # "closed"]

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
