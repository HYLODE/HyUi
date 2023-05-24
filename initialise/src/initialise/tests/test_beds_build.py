import pandas as pd

from initialise.beds_build import _merge_star_and_caboodle_beds

department_samples = [
    "UCH T03 INTENSIVE CARE",
    "UCH T06 HEAD (T06H)",
    "GWB L01 CRITICAL CARE",
    "WMS W01 CRITICAL CARE",
]

virtual_room_samples = [
    "WAITING",
    "WAIT",
    "POOL ROOM",
    "LOUNGE",
]

virtual_bed_samples = [
    "POOL",
    "NONE",
    "ENDO",
    "IMG",
]


def test_bed_build() -> None:
    star_locations = {
        "loc_id": [3, 2, 1, 0],
        "location": ["a", "b", "c", "d"],
        "hl7_department": ["a", "b", "c", "d"],
        "hl7_room": ["a", "b", "c", "d"],
        "hl7_bed": ["a", "b", "c", "d"],
        "lo.department_id": [3, 2, 1, 0],
        "lo.room_id": [3, 2, 1, 0],
        "lo.bed_id": [3, 2, 1, 0],
        "department": department_samples,
        "dept.speciality": ["a", "b", "c", "d"],
        "room": ["a", "b", "c", "d"],
    }

    caboodle_departments = {
        "department_key": [1, 2, 3, 4],
        "bed_epic_id": ["a", "b", "c", "d"],
        "name": ["a", "b", "c", "d"],
        "department_name": department_samples,
        "room_name": ["a", "b", "c", "d"],
        "bed_name": [3, 2, 1, 0],
        "bed_in_census": [3, 2, 1, 0],
        "is_room": [1, 1, 1, 1],
        "is_care_area": ["a", "b", "c", "d"],
        "department_external_name": ["a", "b", "c", "d"],
        "department_speciality": ["a", "b", "c", "d"],
        "department_type": ["a", "b", "c", "d"],
        "department_service_grouper": ["a", "b", "c", "d"],
        "department_level_of_care_grouper": ["a", "b", "c", "d"],
        "location_name": ["a", "b", "c", "d"],
        "parent_location_name": ["a", "b", "c", "d"],
        "creation_instant": [
            "2023-01-14 11:30:00+00:00",
            "2023-01-14 10:45:00+00:00",
            "2023-01-14 10:30:00+00:00",
            "2023-01-14 09:45:00+00:00",
        ],
        "last_updated_instant": [
            "2023-01-14 11:40:00+00:00",
            "2023-01-14 10:55:00+00:00",
            "2023-01-14 10:40:00+00:00",
            "2023-01-14 09:55:00+00:00",
        ],
    }
    star_df = pd.DataFrame.from_dict(star_locations)
    caboodle_df = pd.DataFrame.from_dict(caboodle_departments)

    merged_df = _merge_star_and_caboodle_beds(star_df, caboodle_df)

    assert not merged_df.empty


def test_bed_build_remove_departments_not_of_interest() -> None:
    star_locations = {
        "loc_id": [3, 2, 1, 0],
        "location": ["a", "b", "c", "d"],
        "hl7_department": ["a", "b", "c", "d"],
        "hl7_room": ["a", "b", "c", "d"],
        "hl7_bed": ["a", "b", "c", "d"],
        "lo.department_id": [3, 2, 1, 0],
        "lo.room_id": [3, 2, 1, 0],
        "lo.bed_id": [3, 2, 1, 0],
        "department": ["a", "b", "c", department_samples[-1]],
        "dept.speciality": ["a", "b", "c", "d"],
        "room": ["a", "b", "c", "d"],
    }

    caboodle_departments = {
        "department_key": [1, 2, 3, 4],
        "bed_epic_id": ["a", "b", "c", "d"],
        "name": ["a", "b", "c", "d"],
        "department_name": department_samples,
        "room_name": ["a", "b", "c", "d"],
        "bed_name": [3, 2, 1, 0],
        "bed_in_census": [3, 2, 1, 0],
        "is_room": [1, 1, 1, 1],
        "is_care_area": ["a", "b", "c", "d"],
        "department_external_name": ["a", "b", "c", "d"],
        "department_speciality": ["a", "b", "c", "d"],
        "department_type": ["a", "b", "c", "d"],
        "department_service_grouper": ["a", "b", "c", "d"],
        "department_level_of_care_grouper": ["a", "b", "c", "d"],
        "location_name": ["a", "b", "c", "d"],
        "parent_location_name": ["a", "b", "c", "d"],
        "creation_instant": [
            "2023-01-14 11:30:00+00:00",
            "2023-01-14 10:45:00+00:00",
            "2023-01-14 10:30:00+00:00",
            "2023-01-14 09:45:00+00:00",
        ],
        "last_updated_instant": [
            "2023-01-14 11:40:00+00:00",
            "2023-01-14 10:55:00+00:00",
            "2023-01-14 10:40:00+00:00",
            "2023-01-14 09:55:00+00:00",
        ],
    }
    star_df = pd.DataFrame.from_dict(star_locations)
    caboodle_df = pd.DataFrame.from_dict(caboodle_departments)

    merged_df = _merge_star_and_caboodle_beds(star_df, caboodle_df)

    # Only one department of interest in star
    # After inner join expect only one row in dataframe
    assert len(merged_df) == 1


def test_bed_build_remove_virtual_rooms() -> None:
    star_locations = {
        "loc_id": [3, 2, 1, 0],
        "location": ["a", "b", "c", "d"],
        "hl7_department": ["a", "b", "c", "d"],
        "hl7_room": ["WAIT", "LOUNGE", "c", "WAITING"],
        "hl7_bed": ["a", "b", "c", "d"],
        "lo.department_id": [3, 2, 1, 0],
        "lo.room_id": [3, 2, 1, 0],
        "lo.bed_id": [3, 2, 1, 0],
        "department": ["a", "b", department_samples[-2], department_samples[-1]],
        "dept.speciality": ["a", "b", "c", "d"],
        "room": ["a", "b", "c", "d"],
    }

    caboodle_departments = {
        "department_key": [1, 2, 3, 4],
        "bed_epic_id": ["a", "b", "c", "d"],
        "name": ["a", "b", "c", "d"],
        "department_name": department_samples,
        "room_name": ["a", "b", "c", "d"],
        "bed_name": [3, 2, 1, 0],
        "bed_in_census": [3, 2, 1, 0],
        "is_room": [1, 1, 1, 1],
        "is_care_area": ["a", "b", "c", "d"],
        "department_external_name": ["a", "b", "c", "d"],
        "department_speciality": ["a", "b", "c", "d"],
        "department_type": ["a", "b", "c", "d"],
        "department_service_grouper": ["a", "b", "c", "d"],
        "department_level_of_care_grouper": ["a", "b", "c", "d"],
        "location_name": ["a", "b", "c", "d"],
        "parent_location_name": ["a", "b", "c", "d"],
        "creation_instant": [
            "2023-01-14 11:30:00+00:00",
            "2023-01-14 10:45:00+00:00",
            "2023-01-14 10:30:00+00:00",
            "2023-01-14 09:45:00+00:00",
        ],
        "last_updated_instant": [
            "2023-01-14 11:40:00+00:00",
            "2023-01-14 10:55:00+00:00",
            "2023-01-14 10:40:00+00:00",
            "2023-01-14 09:55:00+00:00",
        ],
    }
    star_df = pd.DataFrame.from_dict(star_locations)
    caboodle_df = pd.DataFrame.from_dict(caboodle_departments)

    merged_df = _merge_star_and_caboodle_beds(star_df, caboodle_df)

    assert merged_df.loc[0, "department_name"] == "GWB L01 CRITICAL CARE"


def test_bed_build_remove_virtual_beds() -> None:
    star_locations = {
        "loc_id": [3, 2, 1, 0],
        "location": ["a", "b", "c", "d"],
        "hl7_department": ["a", "b", "c", "d"],
        "hl7_room": ["a", "b", "c", "d"],
        "hl7_bed": [
            "a",
            virtual_bed_samples[0],
            virtual_bed_samples[1],
            virtual_bed_samples[2],
        ],
        "lo.department_id": [3, 2, 1, 0],
        "lo.room_id": [3, 2, 1, 0],
        "lo.bed_id": [3, 2, 1, 0],
        "department": [
            department_samples[0],
            department_samples[1],
            department_samples[-2],
            department_samples[-1],
        ],
        "dept.speciality": ["a", "b", "c", "d"],
        "room": ["a", "b", "c", "d"],
    }

    caboodle_departments = {
        "department_key": [1, 2, 3, 4],
        "bed_epic_id": ["a", "b", "c", "d"],
        "name": ["a", "b", "c", "d"],
        "department_name": department_samples,
        "room_name": ["a", "b", "c", "d"],
        "bed_name": [3, 2, 1, 0],
        "bed_in_census": [3, 2, 1, 0],
        "is_room": [1, 1, 1, 1],
        "is_care_area": ["a", "b", "c", "d"],
        "department_external_name": ["a", "b", "c", "d"],
        "department_speciality": ["a", "b", "c", "d"],
        "department_type": ["a", "b", "c", "d"],
        "department_service_grouper": ["a", "b", "c", "d"],
        "department_level_of_care_grouper": ["a", "b", "c", "d"],
        "location_name": ["a", "b", "c", "d"],
        "parent_location_name": ["a", "b", "c", "d"],
        "creation_instant": [
            "2023-01-14 11:30:00+00:00",
            "2023-01-14 10:45:00+00:00",
            "2023-01-14 10:30:00+00:00",
            "2023-01-14 09:45:00+00:00",
        ],
        "last_updated_instant": [
            "2023-01-14 11:40:00+00:00",
            "2023-01-14 10:55:00+00:00",
            "2023-01-14 10:40:00+00:00",
            "2023-01-14 09:55:00+00:00",
        ],
    }
    star_df = pd.DataFrame.from_dict(star_locations)
    caboodle_df = pd.DataFrame.from_dict(caboodle_departments)

    merged_df = _merge_star_and_caboodle_beds(star_df, caboodle_df)

    assert len(merged_df) == 1
    assert merged_df.loc[0, "department"] == department_samples[0]
    assert merged_df.loc[0, "hl7_bed"] == "a"
