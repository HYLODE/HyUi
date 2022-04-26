# tests/test_environment.py
import pytest
from dotenv import find_dotenv

def f():
    raise SystemExit(1)

def test_mytest():
    with pytest.raises(SystemExit):
        f()

def test_dev_environment():
    """
    GIVEN
    WHEN you check the environment
    THEN you find a .env file and settings
    """
    assert find_dotenv() != ''

