# src/main.py
from collections import namedtuple
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseSettings
from sqlmodel import Session, create_engine, select

from models import (
    Consultation_Type,
    Consultation_Type_Read,
    ConsultsED,
)


class Settings(BaseSettings):
    UDS_HOST: str
    UDS_USER: str
    UDS_PWD: str


settings = Settings()
postgresql_url = (
    f"postgresql://{settings.UDS_USER}:{settings.UDS_PWD}@{settings.UDS_HOST}:5432/uds"
)
engine = create_engine(postgresql_url, echo=True)


def select_ConsultationType():
    with Session(engine) as session:
        statement = select(Consultation_Type).limit(3)
        results = session.exec(statement)
        for res in results:
            print(res)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()
# prove that connection works
# select_ConsultationType()


@app.get("/consultation_types/", response_model=List[Consultation_Type_Read])
def read_consultation_types(
    *,
    session: Session = Depends(get_session),
):
    statement = select(Consultation_Type).limit(3)
    print(f"*** STATEMENT: {statement}")
    results = session.exec(statement).all()
    print(f"*** RESULTS: {results}")
    return results


@app.get("/consultation_types/{id}", response_model=Consultation_Type_Read)
def read_consultation_type(
    *,
    session: Session = Depends(get_session),
    id: str,
):
    consultation_type = session.get(Consultation_Type, id)
    if not consultation_type:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cons type id not found")
    return consultation_type


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
    q = Path("query.sql").read_text()
    results = session.execute(q)
    print(results.keys())
    # print(results.fetchall())
    Record = namedtuple("Record", results.keys())
    records = [Record(*r) for r in results.fetchall()]
    print(records)
    return records


@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}
