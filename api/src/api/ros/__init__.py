# src/api/ros/__init__.py
"""
ROS screening dashboard
"""

from pathlib import Path

QUERY_LIVE_PATH = Path(__file__).resolve().parent / "live.sql"
QUERY_MOCK_PATH = Path(__file__).resolve().parent / "mock.sql"
