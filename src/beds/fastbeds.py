from datetime import datetime

from sqlalchemy import Column, String, Float, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi_crudrouter import SQLAlchemyCRUDRouter

app = FastAPI()
engine = create_engine("sqlite:///./beds.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


class BedCreate(BaseModel):
    location_id: int
    location_string: str
    # dept: str
    # speciality: str
    # room: str
    # bed: str
    # admission_time: datetime
    # discharge_time: datetime
    # inferred_admission: bool
    # inferred_discharge: bool


class Bed(BedCreate):
    id: int

    class Config:
        orm_mode = True


class BedModel(Base):
    __tablename__ = "beds"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer)
    location_string = Column(String)


Base.metadata.create_all(bind=engine)

router = SQLAlchemyCRUDRouter(
    schema=Bed,
    create_schema=BedCreate,
    db_model=BedModel,
    db=get_db,
    prefix="bed",
)


app.include_router(router)
