# src/api/sitrep/__init__.py
"""
Results from Sitrep API
eg.

http://172.16.149.205:5006/icu/live/{ward}/ui

"""
from pathlib import Path

QUERY_LIVE_PATH = Path(__file__).resolve().parent / "live.sql"
QUERY_MOCK_PATH = Path(__file__).resolve().parent / "mock.sql"
