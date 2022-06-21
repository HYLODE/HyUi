# src/main.py
# TODO: how to dynamically import a python module
# from api.models import ResultsRead
import importlib
from collections import namedtuple
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine

from config.settings import settings  # type: ignore
from utils import gen_module_path, get_model_from_route  # type: ignore

MODULE_ROOT = settings.MODULE_ROOT
ROUTES = settings.ROUTES


def get_emap_session():
    with Session(emap_engine) as emap_session:
        yield emap_session


def get_caboodle_session():
    with Session(caboodle_engine) as caboodle_session:
        yield caboodle_session


def prepare_query(module: str, env: str = settings.ENV) -> str:
    choice = {"prod": "LIVE", "dev": "MOCK"}
    module_path = gen_module_path(module)
    query_name = f"QUERY_{choice[env]}_PATH"
    try:
        q = getattr(importlib.import_module(module_path), query_name)
    except AttributeError as e:
        print(
            f"!!! Check that you have provided a SQL file {choice[env].lower()}.sql in src/api/{module}"  # noqa
        )
        raise e
    print(f"--- INFO: running {choice[env]} query")
    return Path(q).read_text()


emap_engine = create_engine(settings.DB_URL, echo=True)
caboodle_engine = create_engine(settings.CABOODLE_URL, echo=True)

app = FastAPI()

# ======
# ROUTES
# ======


# smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}


ConsultsRead = get_model_from_route("Consults", "Read")


@app.get("/consults", response_model=List[ConsultsRead])  # type: ignore
def read_consults(session: Session = Depends(get_emap_session)):
    """
    Returns Consults data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query("consults")
    results = session.execute(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


SitrepRead = get_model_from_route("Sitrep", "Read")


@app.get("/sitrep", response_model=List[SitrepRead])  # type: ignore
def read_sitrep(session: Session = Depends(get_emap_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("sitrep")
    results = session.execute(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


CensusRead = get_model_from_route("Census", "Read")


@app.get("/census", response_model=List[CensusRead])  # type: ignore
def read_census(session: Session = Depends(get_emap_session)):
    """
    Returns Census data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("census")
    results = session.execute(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


ElectivesRead = get_model_from_route("Electives", "Read")


@app.get("/electives", response_model=List[ElectivesRead])  # type: ignore
def read_electives(session: Session = Depends(get_caboodle_session)):
    """
    Returns Electives data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    TODO: need to add logic to join patient identifiers from EMAP
    """
    q = prepare_query("electives")
    results = session.execute(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
