from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from pydantic import BaseSettings
import arrow

class Settings(BaseSettings):
    EMAP_DB_HOST: str
    UDS_PWD: str

    
class Consultation_Type_Base(SQLModel):
    #stored_from: datetime
    valid_from: datetime
    code: str
    name: str
    

class Consultation_Type(Consultation_Type_Base, table=True):
    __table_args__ = {'schema': 'star'}
    consultation_type_id: Optional[int] = Field(default=None, primary_key=True)
    

class Consultation_Type_Read(Consultation_Type_Base):
    consultation_type_id: int


settings = Settings()

postgresql_url = f"postgresql://sharris9:{settings.UDS_PWD}@{settings.EMAP_DB_HOST}:5432/uds"
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


@app.get("/consultation_types/", response_model=List[Consultation_Type_Read])
def read_consultation_types(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=10, lte=10),
):
    consultation_types = session.exec(select(Consultation_Type).offset(offset).limit(limit)).all()
    return consultation_types
