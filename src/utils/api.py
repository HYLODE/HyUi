import pandas as pd
from sqlmodel import Session, create_engine
from pydantic import BaseModel, parse_obj_as
from typing import List

from config.settings import settings  # type: ignore

emap_engine = create_engine(settings.STAR_URL, echo=True)
caboodle_engine = create_engine(settings.CABOODLE_URL, echo=True)


def get_caboodle_session():
    with Session(caboodle_engine) as caboodle_session:
        yield caboodle_session


def get_emap_session():
    with Session(emap_engine) as emap_session:
        yield emap_session


def pydantic_dataframe(df: pd.DataFrame, model: BaseModel) -> pd.DataFrame:
    """
    round trip from dataframe to dictionary to records back to dataframe
    just to use the data validation properties of pydantic!

    :param      df:     { parameter_description }
    :type       df:     { type_description }
    :param      model:  The model
    :type       model:  BaseModel

    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    l_of_d = df.to_dict(orient="records")
    l_of_r = parse_obj_as(List[model], l_of_d)  # type: ignore
    res = pd.DataFrame.from_dict([r.dict() for r in l_of_r])
    return res
