from datetime import datetime
from typing import Optional

import arrow
from pydantic import BaseModel


class IcuDischarge(BaseModel):
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

    prediction_id: int  # = Field(primary_key=True)
    episode_slice_id: int
    model_name: str
    model_version: int
    prediction_as_real: float
    predict_dt: datetime


class EmTap(BaseModel):  # , table=True):  # type: ignore
    """
     Hymind Emergency Taps
     e.g.

    {
       "bed_count": 0,
       "probability": 0.018392433908071763,
       "predict_dt": "2022-08-08T07:48:24.757274+01:00",
       "model_name": "tap_nonelective_tower",
       "model_version": 1,
       "run_id": "1e44565aa34e4b16970d1e5598b9a028",
       "horizon_dt": "2022-08-08T00:00:00+01:00"
     },
     via
     ```python
     json_data = json.dumps({
         "horizon_dt": date.today().strftime('%Y-%m-%dT%H:%M:%S.%f'),
         "department": "tower",
     })
     response = requests.post("http://uclvlddpragae08:5230/predict/", json_data)
     response.status_code
     ```
    """

    bed_count: int  # = Field(primary_key=True)
    probability: float
    predict_dt: datetime
    model_name: str
    model_version: int
    run_id: str
    horizon_dt: datetime


class ElTap(BaseModel):  # , table=True):  # type: ignore
    """
    Hymind Elective Tap
    e.g.

    {'bed_count': 0,
    'probability': 0.4886959420284716,
    'predict_dt': '2022-08-08T07:07:58.644806+01:00',
    'model_name': 'tap_elective_tower',
    'model_version': 1,
    'run_id': '71f4264cd52d416fbf45ebafdb599160',
    'horizon_dt': '2022-08-10T07:07:38+01:00',
    'inputs': '{"model_function":"binom", "date":1.660111658e+18,
        "icu_counts":0, "noticu_counts":0, "wkday":2,"N":12}'
    },
    via
    ```python
    when = arrow.now().shift(days=2).format("YYYY-MM-DDTHH:mm:ss")
    data = json.dumps({
        "horizon_dt": when,
        "department": "tower",
    })
    requests.post("http://uclvlddpragae08:5219/predict/", data).json()
    """

    # you could go further and specify the nested dictionary model
    # https://stackoverflow.com/a/63259907/992999
    bed_count: int  # = Field(primary_key=True)
    probability: float
    predict_dt: datetime
    model_name: str
    model_version: int
    run_id: str
    horizon_dt: datetime
    inputs: Optional[str]


class EmElTapPostBody(BaseModel):
    horizon_dt: datetime = arrow.now().shift(days=1).format("YYYY-MM-DDTHH:mm:ss")
    department: str = "tower"
