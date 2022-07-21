# src/api/perrt/__init__.py
"""
Inpatients with vitals
The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from pathlib import Path

QUERY_LIVE_PATH = Path(__file__).resolve().parent / "live.sql"
QUERY_MOCK_PATH = Path(__file__).resolve().parent / "mock.sql"
