# src/main.py
from collections import namedtuple
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Session, create_engine, select

from config.settings import settings

from api.models import (
    Consultation_Type,
    Consultation_Type_Read,
    ConsultsED,
)


engine = create_engine(settings.DB_URL, echo=True)


def prepare_query(env=settings.ENV) -> str:
    if env == "prod":
        q = "api/query-live.sql"
    else:
        q = "api/query-mock.sql"
    return Path(q).read_text()


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.get("/consultations_ed/", response_model=List[ConsultsED])
def read_consults_ed(
    *,
    session: Session = Depends(get_session),
):
    """
    Returns consults for patients in ED
    alongside the most recent ED location for that patient
    where that ED location occupied in the last 24h
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
