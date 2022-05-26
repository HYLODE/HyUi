import os
from pathlib import Path
import pytest
import pandas as pd
from mock import mock


@pytest.mark.smoke
def test_mock_data_exists():
    """Confirm HDF file with mock data exists"""
    f = Path(os.getenv("DIR_SRC")) / "mock" / "mock.h5"
    assert f.is_file()


def test_mock_constants():
    """Confirm global constants built"""

    assert mock.SYNTH_HDF_FILE is not None
    assert isinstance(mock.SYNTH_HDF_FILE, Path)
    assert mock.SYNTH_HDF_FILE.is_file()

    assert mock.SYNTH_SQLITE_FILE is not None
    assert isinstance(mock.SYNTH_SQLITE_FILE, Path)
    assert mock.SYNTH_SQLITE_FILE.is_file()

    assert isinstance(mock.SYNTH_SQLITE_URL, str)
    assert isinstance(mock.SYNTH_SQLITE_MEM, str)


def test_make_mock_df():
    df = mock.make_mock_df()
    assert isinstance(df, pd.DataFrame)
    assert df.empty is False


def test_make_mock_df_nofile():
    with pytest.raises(AssertionError):
        not_a_file = Path(__file__) / "not_a_file.foo"
        mock.make_mock_df(f=not_a_file)
