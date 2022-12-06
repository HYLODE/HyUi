"""
Entry point and main file for the FastAPI backend
"""

from fastapi import FastAPI, APIRouter
from fastapi.responses import ORJSONResponse

from api.bedbones.router import (
    mock_router as mock_bedbones_router,
    router as bedbones_router,
)
from api.census.router import mock_router as mock_census_router, router as census_router
from api.consults.router import router as consults_router
from api.ed.router import mock_router as mock_ed_router, router as ed_router
from api.electives.router import (
    mock_router as mock_electives_router,
    router as electives_router,
)

from api.demo.router import (
    router as demo_router,
    mock_router as mock_demo_router,
)

from api.hospital.router import (
    mock_router as mock_hospital_router,
    router as hospital_router,
)
from api.hymind.router import router as hymind_router
from api.perrt.router import mock_router as mock_perrt_router, router as perrt_router
from api.ros.router import router as ros_router
from api.sitrep.router import mock_router as mock_sitrep_router, router as sitrep_router

app = FastAPI(default_response_class=ORJSONResponse)
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

app.include_router(perrt_router)
mock_router.include_router(mock_perrt_router)

app.include_router(ed_router)
mock_router.include_router(mock_ed_router)

app.include_router(bedbones_router)
mock_router.include_router(mock_bedbones_router)

app.include_router(consults_router)

app.include_router(ros_router)
app.include_router(hymind_router)

# Finally include the mock router.
app.include_router(mock_router)


@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
