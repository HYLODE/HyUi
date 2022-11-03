from datetime import date, datetime

from api.convert import to_data_frame
from api.electives.wrangle import prepare_electives
from api.main import app
from fastapi.testclient import TestClient

from models.electives import (
    ElectiveRow,
    ElectivePostOpDestinationRow,
    ElectivePreassessRow,
)

client = TestClient(app)


def test_get_mock_electives():
    response = client.get("/mock/electives")
    assert response.status_code == 200


def test_prepare_electives():
    # This is currently just a placeholder test to ensure all the correct
    # columns are described.
    # TODO: Improve these tests.
    electives = [
        ElectiveRow.parse_obj(
            {
                "PatientDurableKey": "keya",
                "PrimaryMrn": "mrn",
                "SurgicalCaseEpicId": 1,
                "Canceled": False,
                "SurgicalService": "service",
                "AgeInYears": 23,
                "Sex": "Male",
                "FirstName": "Joe",
                "LastName": "Blogs",
                "RoomName": "Room1",
                "SurgeryDate": date(2002, 2, 3),
                "PatientFriendlyName": "BIG SCARY OP",
                "PlannedOperationStartInstant": datetime(2022, 2, 3, 10, 0, 0),
            }
        )
    ]
    electives_df = to_data_frame(electives, ElectiveRow)

    post_op_destinations = [
        ElectivePostOpDestinationRow.parse_obj(
            {"pod_orc": "pod_orc_a", "or_case_id": 1}
        )
    ]
    post_op_destinations_df = to_data_frame(
        post_op_destinations, ElectivePostOpDestinationRow
    )

    preassess = [
        ElectivePreassessRow.parse_obj(
            {
                "PatientDurableKey": "keya",
                "Name": "name",
                "CreationInstant": "2022-07-22 15:04:39.000000",
                "StringValue": "Inpatient Ward",
            }
        )
    ]
    preassess_df = to_data_frame(preassess, ElectivePreassessRow)

    merged_df = prepare_electives(electives_df, post_op_destinations_df, preassess_df)
    assert len(merged_df.index) > 0
