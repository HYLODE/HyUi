# ./src/api/settings_src.py
# project wide settings are loaded via ./.envrc and ./.secrets
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator

PORT_JUPYTER = "8091"

PORT_COMMANDLINE_API = "8092"
PORT_COMMANDLINE_APP = "8093"

PORT_DOCKER_API = "8094"
PORT_DOCKER_APP = "8095"

BASE_URL_DEV = "http://127.0.0.1"
BASE_URL_GAE = "http://172.16.149.202"  # UCLVLDDPRAGAE07
BASE_URL_DOCKER_APP = "http://apps"
BASE_URL_DOCKER_API = "http://api"


class ModuleNames(str, Enum):
    """
    Class that defines routes for each module
    """

    consults = "consults"
    sitrep = "sitrep"


class Environments(str, Enum):
    """
    Recognised evironments
    """

    dev = "dev"
    prod = "prod"


class Settings(BaseSettings):

    ENV: Environments = Environments.dev
    DOCKER: bool = False

    UDS_HOST: Optional[str]
    UDS_USER: Optional[str]
    UDS_PWD: Optional[str]
    UDS_DB: Optional[str]

    DB_URL: Optional[str]
    DB_POSTGRES_SCHEMA = "star"

    BASE_URL: Optional[str]
    API_URL: Optional[str]
    APP_URL: Optional[str]

    MODULE_ROOT: str = "api"  # for building paths to modules e.g. ./src/api
    ROUTES = ModuleNames = ModuleNames._member_names_

    @validator("ENV", pre=True)
    def environment_choice_is_valid(cls, v):
        # b/c when read from .secrets a \r (carriage return) is appended
        return v.rstrip()

    @validator("DB_URL")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if values.get("ENV") == "dev":
            db_path = Path(__file__).resolve().parents[1].absolute() / "mock"
            db_url = f"sqlite:///{db_path.as_posix()}/mock.db"
            return db_url
        else:
            return PostgresDsn.build(
                # TODO: refactor postgres dependency
                scheme="postgresql+psycopg2",
                user=values.get("UDS_USER"),
                password=values.get("UDS_PWD"),
                host=values.get("UDS_HOST"),
                path=f"/{values.get('UDS_DB') or ''}",
            )

    @validator("BASE_URL")
    def assemble_base_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        Selects and assembles the base URL for the application depending on
        the environment
        """
        if values.get("ENV", "dev").lower() == "dev":
            return BASE_URL_DEV
        else:
            return BASE_URL_GAE

    @validator("API_URL")
    def assemble_api_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        Assemble URL for API depending on context to be used by dash app
        - production AND external API
        - production AND internal API (via docker-compose)
        - development AND internal API (via docker-compose)
        - development AND local dev API (FastAPI app run from commandline)


        :returns:   Base URL for API to be used by Frontend
        :rtype:     str
        """
        if values.get("ENV") == "prod":
            return f"{BASE_URL_DOCKER_API}:{PORT_DOCKER_API}"

        if values.get("ENV") == "dev":
            if values.get("DOCKER") is True:
                return f"{BASE_URL_DOCKER_API}:{PORT_DOCKER_API}"
            else:
                return f"{BASE_URL_DEV}:{PORT_COMMANDLINE_API}"

    @validator("APP_URL")
    def assemble_app_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        :returns:   Base URL for the APP (esp for testing)
        :rtype:     str
        """
        if values.get("ENV") == "prod":
            return f"{BASE_URL_GAE}:{PORT_DOCKER_APP}"

        if values.get("ENV") == "dev":
            if values.get("DOCKER") is True:
                return f"{BASE_URL_DOCKER_APP}:{PORT_DOCKER_APP}"
            else:
                return f"{BASE_URL_DEV}:{PORT_COMMANDLINE_APP}"

    class Config:
        case_sensitive = True


settings = Settings()
# print(settings.SERVICES)
