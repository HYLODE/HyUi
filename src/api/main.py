# src/main.py
from collections import namedtuple
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine

from config.settings import settings

from api.models import ResultsRead

QUERY_LIVE_PATH = Path(__file__).resolve().parent / "query-live.sql"
QUERY_MOCK_PATH = Path(__file__).resolve().parent / "query-mock.sql"

engine = create_engine(settings.DB_URL, echo=True)


def prepare_query(env=settings.ENV) -> str:
    if env == "prod":
        q = QUERY_LIVE_PATH
        print("--- INFO: running LIVE query")
    else:
        q = QUERY_MOCK_PATH
        print("--- INFO: running MOCK query")
    return Path(q).read_text()


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.get("/results/", response_model=List[ResultsRead])
def read_results(session: Session = Depends(get_session)):
    """
    Returns Results data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query()
    results = session.execute(q)
    Record = namedtuple("Record", results.keys())
    records = [Record(*r) for r in results.fetchall()]
    return records


# smoke
@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
