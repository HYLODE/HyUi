from models.sitrep import IndividualDischargePrediction


def test_individual_discharge_prediction_alias():
    prediction = IndividualDischargePrediction.parse_obj(
        {
            "episode_slice_id": "2",
            "prediction_as_real": 0.23,
        }
    )
    assert prediction.prediction == 0.23
