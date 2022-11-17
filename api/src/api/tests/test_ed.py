from datetime import datetime

from api.ed.router import adjust_for_model_specific_times


def test_adjust_for_model_specific_times():
    t = datetime(2022, 10, 12, 23, 10, 16, 10)
    adjusted_t = adjust_for_model_specific_times(t)
    assert adjusted_t == datetime(2022, 10, 12, 22, 30)


def test_adjust_for_model_specific_times_previous_day():
    t = datetime(2022, 10, 12, 6, 10, 16, 10)
    adjusted_t = adjust_for_model_specific_times(t)
    assert adjusted_t == datetime(2022, 10, 11, 22, 30)
