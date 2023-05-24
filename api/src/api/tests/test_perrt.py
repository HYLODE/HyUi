# type: ignore
import pandas as pd
from fastapi.testclient import TestClient

import api.perrt.wrangle as wng
from api.main import app
from models.perrt import (
    EmapVitalsLong,
    EmapVitalsWide,
)

client = TestClient(app)


def test_get_mock_vitals_long() -> None:
    response = client.get("/mock/perrt/vitals/long")
    assert response.status_code == 200

    rows = [EmapVitalsLong.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_vitals_wide() -> None:
    response = client.get("/mock/perrt/vitals/wide")
    assert response.status_code == 200

    rows = [EmapVitalsWide.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_news_as_int() -> None:
    df = pd.DataFrame(
        {
            "id_in_application": ["NEWS_scale_1", "NEWS_scale_2"],
            "value_as_text": ["1", "2"],
            "value": [11.0, 22.0],
        }
    )

    df_r = wng._news_as_int(df)
    pd.testing.assert_series_equal(
        df_r["value"], pd.Series([1.0, 2.0]), check_names=False
    )


def test_news_as_int_missing_news_scale_2() -> None:
    df = pd.DataFrame(
        {"id_in_application": ["NEWS_scale_2"], "value_as_text": ["2"], "value": [22.0]}
    )
    df_r = wng._news_as_int(df)
    pd.testing.assert_series_equal(df_r["value"], pd.Series([2.0]), check_names=False)


def test_wrangle() -> None:
    df = pd.DataFrame(
        {
            "hospital_visit_id": [91, 92],
            "encounter": ["910", "920"],
            # two news_scale_1_max, # no news_scale_2_max
            "id_in_application": [28315, 28315],
            "value_as_text": ["1", "2"],
            "value_as_real": [11.0, 22.0],
        }
    )
    df_r = wng.wrangle(df)
    pd.testing.assert_series_equal(
        df_r["news_scale_1_max"], pd.Series([1.0, 2.0]), check_names=False
    )
