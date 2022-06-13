# tests/test_smoke_base.py
# this file should NOT contain any imports from src
# we are just trying to check the environment is set-up correctly
import os
import sys
from pathlib import Path

import pytest

from config.settings import settings


@pytest.mark.smoke
def test_python_version():
    assert sys.version_info[0] == 3
    assert sys.version_info[1] >= 9


@pytest.mark.smoke
@pytest.mark.skipif(
    # .env exists outside docker and its contents are loaded by docker-compose
    os.getenv("DOCKER", "False") == "True",
    reason="Skipping test that should not be run by GitHub Actions",
)
def test_env_file_exists():
    """Secrets should be kept in .env at project root"""
    p = Path(__file__).resolve().parents[3] / ".env"
    assert p.is_file()


@pytest.mark.smoke
def test_the_environment_is_set():
    assert settings.ENV in ["dev", "prod"]


# FIXME: fails b/c settings are established before the monkeypath
# monkeypatch set-up in ./conftest.py
@pytest.mark.skip(reason="fails b/c settings defined before monkeypatch")
def test_settings_uds_user(mock_env_uds_vars):
    assert settings.EMAP_DB_USER == "BigBird"
    assert settings.EMAP_DB_PWD == "Sesame"
    assert settings.EMAP_DB_HOST == "172.16.149.132"
