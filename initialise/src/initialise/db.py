from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from initialise.config import get_db_settings


@lru_cache()
def caboodle_engine() -> Engine:
    settings = get_db_settings()
    return create_engine(settings.caboodle_dsn, echo=False, future=False)


@lru_cache()
def star_engine() -> Engine:
    settings = get_db_settings()
    return create_engine(settings.star_dsn, echo=False, future=False)
