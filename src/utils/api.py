from sqlmodel import Session, create_engine

from config.settings import settings  # type: ignore

emap_engine = create_engine(settings.STAR_URL, echo=True)
caboodle_engine = create_engine(settings.CABOODLE_URL, echo=True)


def get_caboodle_session():
    with Session(caboodle_engine) as caboodle_session:
        yield caboodle_session


def get_emap_session():
    with Session(emap_engine) as emap_session:
        yield emap_session
