from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.census.router import router as census_router

# from .consults import router as consults
# from .electives import router as electives
# from .perrt import router as perrt
# from .sitrep import router as sitrep
# from .users import router as users
# from .ros import router as ros
# from .census import router as census
# from .hymind import router as hymind

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(census_router)
# app.include_router(consults.router)
# app.include_router(electives.router)
# app.include_router(perrt.router)
# app.include_router(sitrep.router)
# app.include_router(users.router)
# app.include_router(ros.router)

# app.include_router(hymind.router)


# ======
# ROUTES
# ======

# Smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
