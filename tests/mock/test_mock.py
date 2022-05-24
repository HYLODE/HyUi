import os
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_mock_data_exists():
    """Confirm HDF file with mock data exists"""
    f = Path(os.getenv("DIR_SRC")) / "mock" / "mock.h5"
    assert f.is_file()
