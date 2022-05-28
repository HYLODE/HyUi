# src/main.py
# TODO: how to dynamically import a python module
# from api.models import ResultsRead
import importlib
from collections import namedtuple
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine

from config.settings import settings

MODULE_ROOT = "api"
module_name = "consults"


def gen_module_path(name: str, root: str = MODULE_ROOT) -> str:
    return f"{MODULE_ROOT}.{module_name}"


consults = importlib.import_module(gen_module_path(module_name))

engine = create_engine(settings.DB_URL, echo=True)
app = FastAPI()


def get_session():
    with Session(engine) as session:
        yield session


def prepare_query(module: str, env: str = settings.ENV) -> str:
    choice = {"prod": "LIVE", "dev": "MOCK"}
    module_path = gen_module_path(module)
    query_name = f"QUERY_{choice[env]}_PATH"
    q = getattr(importlib.import_module(module_path), query_name)
    print(f"--- INFO: running {choice[env]} query")
    return Path(q).read_text()


# TODO dynamically create the route
@app.get("/results/", response_model=List[consults.ResultsRead])
def read_results(session: Session = Depends(get_session)):
    """
    Returns Results data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query(module_name)
    results = session.execute(q)
    Record = namedtuple("Record", results.keys())
    records = [Record(*r) for r in results.fetchall()]
    return records


# smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
