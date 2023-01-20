"""
FastAPI APIRouter Dependencies
"""

from fastapi import Response


async def add_cache_control_header(response: Response) -> None:
    response.headers["Cache-control"] = "public, max-age=300"
    # response.headers["Cache-age"] = response.headers["Age"]
