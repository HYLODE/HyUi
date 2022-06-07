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
from utils import gen_module_path  # type: ignore

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
            f"!!! Check that you have provided a SQL file {choice[env].lower()}.sql in src/api/{module}"
        )
        raise e
    print(f"--- INFO: running {choice[env]} query")
    return Path(q).read_text()


def read_factory(module: str):
    """
    Each path returns data as per the Pydantic/SQLModel specificaton in the submodule
    This function generates that path automatically from the names of the modules
    i.e. assumes that the path 'consults' will be served from the ./src/api/consults module
    """
    module_path = gen_module_path(module)
    ModuleRead = f"{module.title()}Read"
    try:
        ResultsRead = getattr(importlib.import_module(module_path), ModuleRead)
    except AttributeError as e:
        print(e)
        print(
            f"!!! Check that you have provided a SQLModel named {ModuleRead} in src/api/{module}"
        )
        raise AttributeError

    @app.get(f"/results/{{module}}", response_model=List[ResultsRead])
    def read_results(
        module: settings.ModuleName, session: Session = Depends(get_session)
    ):
        """
        Returns Results data class populated by query-live/mock
        query preparation depends on the environment so will return
        mock data in dev and live data in prod
        """
        q = prepare_query(module)
        results = session.execute(q)
        Record = namedtuple("Record", results.keys())
        records = [Record(*r) for r in results.fetchall()]
        return records

    return read_results


engine = create_engine(settings.DB_URL, echo=True)
app = FastAPI()

# smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}


# Dynamically generate ROUTES based on modules
for route in ROUTES:
    read_factory(route)
