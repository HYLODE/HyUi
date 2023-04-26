"""
Entry point and main file for the FastAPI backend
"""

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import ORJSONResponse
from fastapi_utils.tasks import repeat_every
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
from api.demo.router import mock_router as mock_demo_router, router as demo_router
from api.hospital.router import (
    mock_router as mock_hospital_router,
    router as hospital_router,
)
from api.hymind.router import (
    router as hymind_router,
    mock_router as mock_hymind_router,
)
from api.perrt.router import mock_router as mock_perrt_router, router as perrt_router
from api.perrt.admission_probability.predictions_script import run_prediction_pipeline
from api.ros.router import router as ros_router

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

app.include_router(perrt_router)
mock_router.include_router(mock_perrt_router)

app.include_router(ed_router)
mock_router.include_router(mock_ed_router)

app.include_router(beds_router)
mock_router.include_router(mock_beds_router)

app.include_router(consults_router)

app.include_router(ros_router)
app.include_router(hymind_router)
mock_router.include_router(mock_hymind_router)

# Finally include the mock router.
app.include_router(mock_router)


@app.on_event("startup")
@repeat_every(seconds=1800, raise_exceptions=False)
def refresh_perrt_icu_admission_predictions() -> None:
    app.state.perrt_icu_adm_predictions = {}
    predictions = run_prediction_pipeline()
    app.state.perrt_icu_adm_predictions = predictions


@app.middleware("http")
async def add_cache_control_header(request: Request, call_next: Any) -> Response:
    response = await call_next(request)
    if "Cache-Control" not in response.headers:
        response.headers["Cache-control"] = "no-cache"
    return response


@app.get("/ping")
async def pong() -> dict[str, str]:
    return {"ping": "hyui pong!"}
