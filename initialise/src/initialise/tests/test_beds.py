import pytest
import json
from initialise.beds import _load_beds_user_defaults
from pathlib import Path


@pytest.fixture(scope="session")
def sample_bed_json(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    sample_data = {
        "department": {0: "GWB"},
        "room": {0: "SR01"},
        "hl7_bed": {0: "SR01-01"},
        "location_id": {0: 1000},
        "location_string": {0: "GWB LOCN"},
        "hl7_department": {0: "1000000"},
        "hl7_room": {0: "GWB ROOM"},
        "department_id": {0: 100},
        "room_id": {0: 10},
        "bed_id": {0: 1},
        "bed_index": {0: 1},
        "floor": {0: 9},
        "location_name": {0: "GRAFTON WAY BUILDING"},
        "bed_number": {0: 1},
        "closed": {0: False},
        "xpos": {0: 10},
        "ypos": {0: 10},
        "blocked": {0: False},
    }

    missing_data = {
        "department": {0: "GWB"},
        "room": {0: "SR01"},
        "hl7_bed": {0: "SR01-01"},
        "location_id": {},
        "location_string": {0: "GWB LOCN"},
        "hl7_department": {0: "1000000"},
        "hl7_room": {0: "GWB ROOM"},
        "department_id": {},
        "room_id": {},
        "bed_id": {},
        "bed_index": {},
        "floor": {0: 9},
        "location_name": {0: "GRAFTON WAY BUILDING"},
        "bed_number": {0: 1},
        "closed": {},
        "xpos": {},
        "ypos": {},
        "blocked": {0: False},
    }

    standard_file = tmp_path_factory.mktemp("data") / "sample_beds.json"  # type: Path
    missing_vals_file = (
        tmp_path_factory.mktemp("data") / "sample_beds_missing.json"
    )  # type: Path
    with open(standard_file, "w") as default_out_file:
        json.dump(sample_data, default_out_file)
    with open(missing_vals_file, "w") as missing_out_file:
        json.dump(missing_data, missing_out_file)

    return {"default": standard_file, "missing": missing_vals_file}


def test_load_beds_user_defaults(sample_bed_json: dict[str, Path]) -> None:
    file_path = Path(sample_bed_json["default"])
    df = _load_beds_user_defaults(file_path)

    assert not df.empty


def test_load_beds_user_missing(sample_bed_json: dict[str, Path]) -> None:
    file_path = Path(sample_bed_json["missing"])
    df = _load_beds_user_defaults(file_path)

    assert len(df) == 1
    assert df.loc[0, "xpos"] == -1
    assert df.loc[0, "location_id"] == -1
    assert df.loc[0, "department_id"] == -1
    assert df.loc[0, "room_id"] == -1
    assert df.loc[0, "bed_id"] == -1
    assert df.loc[0, "bed_index"] == -1
    assert df.loc[0, "xpos"] == -1
    assert df.loc[0, "ypos"] == -1
    assert not df.loc[0, "closed"]
