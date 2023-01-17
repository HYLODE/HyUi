"""
Entry point and main file for the FastAPI backend
"""

from fastapi import Response


# Inject cache control headers
# from https://fastapi.tiangolo.com/tutorial/middleware/
# Can ignore deprecation warnings as they're from Starlette
async def add_cache_control_header(response: Response) -> None:
    response.headers["Cache-control"] = "public, max-age=300"
