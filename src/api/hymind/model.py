# src/api/hymind/model.py
from datetime import date, datetime
from typing import Optional

import arrow
from pydantic import validator
from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


class IcuDischarge(SQLModel, table=True):
    """
    HyMind API ICU discharge predictions
    e.g.
    {
      "prediction_id": 212483,
      "episode_slice_id": 25065,
      "model_name": "bournville_rf",
      "model_version": 3,
      "prediction_as_real": 0.31431410324053705,
      "predict_dt": "2022-08-06T14:02:14.214089+01:00"
    }
    """
    prediction_id: int = Field(primary_key=True)
    episode_slice_id: int
    model_name: str
    model_version: int
    prediction_as_real: float
    predict_dt: datetime
