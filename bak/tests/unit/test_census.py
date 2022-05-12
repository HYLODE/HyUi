import pytest


def test_keys_in_icu_census():

    census_fields = [
        "episode_slice_id",
        "csn",
        "admission_dt",
        "elapsed_los_td",
        "bed_code",
        "bay_code",
        "bay_type",
        "ward_code",
        "mrn",
        "name",
        "dob",
        "admission_age_years",
        "sex",
        "is_proned_1_4h",
        "discharge_ready_1_4h",
        "is_agitated_1_8h",
        "n_inotropes_1_4h",
        "had_nitric_1_8h",
        "had_rrt_1_4h",
        "had_trache_1_12h",
        "vent_type_1_4h",
        "avg_heart_rate_1_24h",
        "max_temp_1_12h",
        "avg_resp_rate_1_24h",
        "wim_1",
    ]
