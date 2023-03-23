from models.taps import TapsPredictor


def test_elective_admissions_prediction_inputs_field_filled() -> None:

    prediction = TapsPredictor.parse_obj(
        {
            "bed_count": 0,
            "probability": 0.59,
            "predict_dt": "2023-03-23T12:00:00.951758+00:00",
            "model_name": "tap_elective_tower",
            "model_version": 1,
            "run_id": "abcdefg",
            "horizon_dt": "2023-03-23T12:00:00.000000+00:00",
            "inputs": '{"model_function":"model","date":date,'
            + '"icu_counts":0,"noticu_counts":0,"wkday":3,"N":1}',
        }
    )
    assert prediction.probability == 0.59
    assert (
        prediction.inputs
        == '{"model_function":"model","date":date,'
        + '"icu_counts":0,"noticu_counts":0,"wkday":3,"N":1}'
    )


def test_elective_admissions_prediction_inputs_field_null() -> None:

    prediction = TapsPredictor.parse_obj(
        {
            "bed_count": 0,
            "probability": 0.75,
            "predict_dt": "2023-03-23T12:00:00.951758+00:00",
            "model_name": "tap_elective_tower",
            "model_version": 1,
            "run_id": "abcdefg",
            "horizon_dt": "2023-03-23T12:00:00.000000+00:00",
            "inputs": None,
        }
    )
    assert prediction.probability == 0.75
    assert prediction.inputs is None
