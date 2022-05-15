# src/main.py 
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from pydantic import BaseSettings
import arrow

class Settings(BaseSettings):
    UDS_HOST: str
    UDS_USER: str
    UDS_PWD: str

    
class Consultation_Type_Base(SQLModel):
    valid_from: datetime
    code: str
    name: Optional[str] = Field(default="")
    

class Consultation_Type(Consultation_Type_Base, table=True):
    __table_args__ = {'schema': 'star'}
    consultation_type_id: Optional[int] = Field(default=None, primary_key=True)
    

class Consultation_Type_Read(Consultation_Type_Base):
    consultation_type_id: int


settings = Settings()

postgresql_url = f"postgresql://{settings.UDS_USER}:{settings.UDS_PWD}@{settings.UDS_HOST}:5432/uds"
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
        raise HTTPException(status_code404, detail="Cons type id not found")
    return consultation_type


@app.get("/ping")
async def pong():
    return {"ping": "hyui pong!"}