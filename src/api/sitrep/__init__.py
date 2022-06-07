# src/api/sitrep/__init__.py
"""
Results from Sitrep API
eg.

http://172.16.149.205:5006/icu/live/{ward}/ui

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""
from pathlib import Path

QUERY_LIVE_PATH = Path(__file__).resolve().parent / "live.sql"
QUERY_MOCK_PATH = Path(__file__).resolve().parent / "mock.sql"
