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


def get_session():
    with Session(engine) as session:
        yield session


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


engine = create_engine(settings.DB_URL, echo=True)
app = FastAPI()

# ======
# ROUTES
# ======


# smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}


ConsultsRead = get_model_from_route("Consults", "Read")


@app.get("/results/consults", response_model=List[ConsultsRead])  # type: ignore
def read_consults(session: Session = Depends(get_session)):
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


@app.get("/results/sitrep", response_model=List[SitrepRead])  # type: ignore
def read_sitrep(session: Session = Depends(get_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)
    TODO: live reads where an API already exists need to bypass the query
    """
    q = prepare_query("sitrep")
    results = session.execute(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
