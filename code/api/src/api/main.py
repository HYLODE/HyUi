from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.census.router import router as census_router
from api.sitrep.router import router as sitrep_router
from api.bedbones.router import router as bedbones_router
from api.electives.router import router as electives_router
from api.consults.router import router as consults_router
from api.perrt.router import router as perrt_router
from api.ros.router import router as ros_router
from api.hymind.router import router as hymind_router


app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(census_router)
app.include_router(bedbones_router)
app.include_router(consults_router)
app.include_router(electives_router)
app.include_router(perrt_router)
app.include_router(sitrep_router)
app.include_router(ros_router)
app.include_router(hymind_router)


@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
