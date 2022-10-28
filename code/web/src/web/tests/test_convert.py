from pydantic import BaseModel

from web.convert import to_data_frame, parse_to_data_frame


class MyModel(BaseModel):
    a: int
    b: str


def test_to_data_frame():
    df = to_data_frame([MyModel(a=1, b="1"), MyModel(a=2, b="2")], MyModel)
    assert len(df.index) == 2
    assert df.iloc[0].a == 1
    assert df.iloc[0].b == "1"
    assert df.iloc[1].a == 2
    assert df.iloc[1].b == "2"


def test_to_data_frame_empty_list():
    df = to_data_frame([], MyModel)
    assert len(df.index) == 0
    assert df.columns.tolist() == ["a", "b"]


def test_parse_to_data_frame():
    df = parse_to_data_frame([dict(a=1, b=1), dict(a=2, b=2)], MyModel)
    assert len(df.index) == 2
    assert df.iloc[0].a == 1
    assert df.iloc[0].b == "1"
    assert df.iloc[1].a == 2
    assert df.iloc[1].b == "2"
