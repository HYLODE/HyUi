from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select, MetaData
from datetime import datetime
from pydantic import BaseSettings
import arrow

class Settings(BaseSettings):
    EMAP_DB_HOST: str
    UDS_PWD: str


class Consultation_Type(SQLModel, table=True):
    #__table_args__ = {'schema': 'star'}
    metadata = MetaData(schema="star")
    consultation_type_id: Optional[int] = Field(default=None, primary_key=True)
    #stored_from: datetime
    #valid_from: datetime
    code: str
    name: str

    
    
class Consultation_Request(SQLModel, table=True):
    #__table_args__ = {'schema': 'star'}
    metadata = MetaData(schema="star")
    consultation_request_id: Optional[int] = Field(default=None, primary_key=True)
    #stored_from: datetime
    valid_from: datetime
    cancelled: bool
    closed_due_to_discharge: bool
    #scheduled_datetime: datetime
    #status_change_datetime: datetime
    # TODO: better way to pass schema into foreign key?
    consultation_type_id: Optional[int] = Field(default=None, foreign_key="consultation_type.consultation_type_id")
    #hospital_visit_id: int
    
    
settings = Settings()

postgresql_url = f"postgresql://sharris9:{settings.UDS_PWD}@{settings.EMAP_DB_HOST}:5432/uds"

engine = create_engine(postgresql_url, echo=True)   


def select_ConsultationType():
    with Session(engine) as session:
        statement = select(Consultation_Type)
        results = session.exec(statement)
        for res in results:
            print(res)
            
def select_ConsultationRequests():
    # use arrow but convert back to datetime 
    # by .datetime method so compatible with type definition
    start_ts = arrow.utcnow().to('Europe/London').shift(hours=-1).datetime
    with Session(engine) as session:
        statement = select(Consultation_Request, Consultation_Type
                          ).join(Consultation_Type
                           ).where(
            Consultation_Request.valid_from >= start_ts)
        results = session.exec(statement)
        for res in results:
            print(res)
        
            
def main():
    select_ConsultationType()
    # select_ConsultationRequests()
    
if __name__ == "__main__":
    main()
