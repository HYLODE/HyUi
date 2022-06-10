from pathlib import Path
import pytest
import pandas as pd
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
from mock import mock
from utils import get_model_from_route


@pytest.mark.smoke
def test_mock_data_exists():
    """Confirm SQLite DB file with mock data exists"""
    f = Path.cwd() / "src" / "mock" / "mock.db"
    assert f.is_file()


def test_mock_constants():
    """Confirm global constants built"""

    assert mock.SYNTH_SQLITE_FILE is not None
    assert isinstance(mock.SYNTH_SQLITE_FILE, Path)
    assert mock.SYNTH_SQLITE_FILE.is_file()

    assert isinstance(mock.SYNTH_SQLITE_URL, str)
    assert isinstance(mock.SYNTH_SQLITE_MEM, str)


def test_make_mock_df_nofile():
    with pytest.raises(AssertionError):
        not_a_file = Path(__file__) / "not_a_file.foo"
        mock.make_mock_df(f=not_a_file)


def test_make_engine():
    engine = mock.make_engine("sqlite://")
    assert str(type(engine)) == "<class 'sqlalchemy.future.engine.Engine'>"


def test_create_mock_table():
    engine = create_engine("sqlite://")

    class Foo(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        spam: str
        eggs: int

    mock.create_mock_table(engine, Foo, drop=False)


def test_insert_into_mock_table():
    engine = create_engine("sqlite://")
    df = pd.DataFrame(
        dict(
            id=[1, 2, 3],
            spam=["a", "b", "c"],
            eggs=[4, 5, 6],
        )
    )

    class FooBar(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        spam: str
        eggs: int

    SQLModel.metadata.create_all(engine)
    status = mock.insert_into_mock_table(engine, df, FooBar)
    assert status == 0


def test_make_mock_db_in_memory(route: str = "sitrep"):
    engine = mock.make_mock_db_in_memory(route)
    model = get_model_from_route(route)
    with Session(engine) as session:
        results = session.exec(select(model))
        result = results.first()
    assert isinstance(result, SQLModel)
