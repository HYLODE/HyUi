# src/main.py
from fastapi import FastAPI

from .census import router as census
from .consults import router as consults
from .electives import router as electives
from .perrt import router as perrt
from .sitrep import router as sitrep
from .users import router as users

app = FastAPI()
app.include_router(census.router)
app.include_router(consults.router)
app.include_router(electives.router)
app.include_router(perrt.router)
app.include_router(sitrep.router)
app.include_router(users.router)


# ======
# ROUTES
# ======

# Smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
