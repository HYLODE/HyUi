# tests/test_smoke_base.py
# this file should NOT contain any imports from src
# we are just trying to check the environment is set-up correctly
import pytest
import sys
import os
from pathlib import Path


@pytest.mark.smoke
def test_python_version():
    assert sys.version_info[0] == 3
    assert sys.version_info[1] >= 9


@pytest.mark.smoke
def test_secrets_file_exists():
    p = Path("./.secrets")
    assert p.is_file()


@pytest.mark.smoke
def test_the_environment_is_set():
    assert os.getenv("ENV") in ["dev", "prod"]
