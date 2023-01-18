"""
Entry point and main file for the FastAPI backend
"""

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import ORJSONResponse
from typing import Any

from api.census.router import router as census_router, mock_router as mock_census_router
from api.sitrep.router import router as sitrep_router, mock_router as mock_sitrep_router
from api.electives.router import (
    router as electives_router,
    mock_router as mock_electives_router,
)
from api.ed.router import (
    router as ed_router,
    mock_router as mock_ed_router,
)

from api.beds.router import (
    router as beds_router,
    mock_router as mock_beds_router,
)
from api.consults.router import router as consults_router
from api.perrt.router import router as perrt_router
from api.ros.router import router as ros_router
from api.hymind.router import router as hymind_router
from api.hospital.router import (
    router as hospital_router,
    mock_router as mock_hospital_router,
)
from api.demo.router import (
    router as demo_router,
    mock_router as mock_demo_router,
)

app = FastAPI(
    default_response_class=ORJSONResponse,
)

mock_router = APIRouter(
    prefix="/mock",
)

app.include_router(demo_router)
mock_router.include_router(mock_demo_router)

app.include_router(hospital_router)
mock_router.include_router(mock_hospital_router)

app.include_router(census_router)
mock_router.include_router(mock_census_router)

app.include_router(sitrep_router)
mock_router.include_router(mock_sitrep_router)

app.include_router(electives_router)
mock_router.include_router(mock_electives_router)

app.include_router(ed_router)
mock_router.include_router(mock_ed_router)

app.include_router(beds_router)
mock_router.include_router(mock_beds_router)

app.include_router(consults_router)

app.include_router(perrt_router)
app.include_router(ros_router)
app.include_router(hymind_router)

# Finally include the mock router.
app.include_router(mock_router)


@app.middleware("http")
async def add_cache_control_header(request: Request, call_next: Any) -> Response:
    response = await call_next(request)
    print(request.body)
    if "x-cache-control" not in request.headers:
        response.headers["Cache-control"] = "public, max-age=300"
    # Can't for some reason parse out request headers...
    else:
        response.headers["Cache-control"] = request.headers["x-cache-control"]
    try:
        if request.headers["X-Varnish-Nuke"] == "1":
            response.headers["Cache-control"] = "no-cache"
    except KeyError:
        # mostly expected behaviour - requests won't have cache control headers
        pass
    return response


@app.get("/ping")
async def pong() -> dict[str, str]:
    return {"ping": "hyui pong!"}
