# type: ignore
from api.main import app
from fastapi.testclient import TestClient

from models.demo import ClarityOrCase

client = TestClient(app)


def test_get_mock_demo():
    response = client.get("/mock/demo/", params={})
    assert response.status_code == 200

    demo_rows = [ClarityOrCase.parse_obj(row) for row in response.json()]
    assert len(demo_rows) > 0
