import pytest

from api.main import app
from fastapi.testclient import TestClient

from models.demo import ClarityOrCase

client = TestClient(app)


def test_get_mock_demo():
    response = client.get("/mock/demo/", params={})
    assert response.status_code == 200

    demo_rows = [ClarityOrCase.parse_obj(row) for row in response.json()]
    assert len(demo_rows) > 0


@pytest.mark.live
def test_get_demo():
    """
    Should only pass when run in the live environment hence the marker
    i.e. when developing locally
    `pytest -v -m 'not live'`

    Should not fail - would suggest no operating in the next 3 days
    :return:
    """
    response = client.get("/demo/", params={"days_ahead": 3})
    assert response.status_code == 200

    demo_rows = [ClarityOrCase.parse_obj(row) for row in response.json()]
    assert len(demo_rows) > 0
