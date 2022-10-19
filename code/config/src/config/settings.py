from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator


class ModuleNames(str, Enum):
    """
    Class that defines routes for each module
    """

    consults = "consults"
    sitrep = "sitrep"
    electives = "electives"
    perrt = "perrt"
    ros = "ros"
    census = "census"
    hymind = "hymind"


class Environments(str, Enum):
    """
    Recognised evironments
    """

    dev = "dev"
    test = "test"
    prod = "prod"


class Settings(BaseSettings):
    """
    Note that the front end app may contain components from multiple sources at
    various stages of maturity so any or all of the dev/test/prod URLs may be in
    use.
    TODO: Also note that the ports are not aligned between staging_red and prod
    """

    ENV: Environments = Environments.dev

    HYUI_USER: str
    HYUI_PASSWORD: str
    SECRET_KEY: str

    BASE_URL_DEV: str  # http://locahost
    BASE_URL_TEST: str  # http://172.16.149.205
    BASE_URL_PROD: str  # http://172.16.149.202

    BASE_URL: str = ""

    DOCKER: bool = False
    VERBOSE: bool = True

    PORT_COMMANDLINE_API: str
    PORT_DOCKER_API: str

    PORT_COMMANDLINE_APP: str
    PORT_DOCKER_APP: str

    PORT_JUPYTER: str

    EMAP_DB_HOST: Optional[str]
    EMAP_DB_USER: Optional[str]
    EMAP_DB_PASSWORD: Optional[str]
    EMAP_DB_NAME: Optional[str]

    DB_POSTGRES_SCHEMA = "star"

    CABOODLE_DB_HOST: Optional[str]
    CABOODLE_DB_USER: Optional[str]
    CABOODLE_DB_PASSWORD: Optional[str]
    CABOODLE_DB_NAME: Optional[str]
    CABOODLE_DB_PORT: Optional[int]

    CLARITY_DB_HOST: Optional[str]
    CLARITY_DB_USER: Optional[str]
    CLARITY_DB_PASSWORD: Optional[str]
    CLARITY_DB_NAME: Optional[str]
    CLARITY_DB_PORT: Optional[int]

    BASEROW_READWRITE_TOKEN: Optional[str]
    BASEROW_PORT: Optional[str]
    PORT_DOCKER_BASEROW: Optional[str]

    MODULE_ROOT: str = "models"  # for building paths to modules e.g. ./src/api
    ROUTES = ModuleNames = ModuleNames._member_names_

    BASE_URL_DOCKER_APP: str = "http://apps"
    BASE_URL_DOCKER_API: str = "http://api"
    BASE_URL_DOCKER_BASEROW: str = "http://baserow"

    # WARNING!
    # The order of variable declaration is important
    # i.e. don't construct a URL containing a PORT if you haven't declared the port yet
    # the variables above of the variables below

    STAR_URL: Optional[str]
    CABOODLE_URL: Optional[str]
    CLARITY_URL: Optional[str]

    API_URL: Optional[str]
    APP_URL: Optional[str]

    BASEROW_URL: Optional[str]
    BASEROW_PUBLIC_URL: Optional[str]

    @validator("ENV", pre=True)
    def environment_choice_is_valid(cls, v):
        # b/c when read from .secrets a \r (carriage return) is appended
        return v.rstrip()

    @validator("BASE_URL", pre=True)
    def select_base_url_from_env(cls, v, values: Dict[str, Any]):
        # b/c when read from .secrets a \r (carriage return) is appended
        if values.get("ENV") == "dev":
            v = values.get("BASE_URL_DEV")
        elif values.get("ENV") == "test":
            v = values.get("BASE_URL_TEST")
        elif values.get("ENV") == "prod":
            v = values.get("BASE_URL_PROD")
        else:
            raise ValueError("Environment not recognised")
        return v.rstrip()

    @validator("STAR_URL")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if values.get("ENV") == "dev":
            db_path = Path(__file__).parents[0] / "resources" / "mock.db"
            return f"sqlite:///{db_path}"

        return PostgresDsn.build(
            # TODO: refactor postgres dependency
            scheme="postgresql+psycopg2",
            user=values.get("EMAP_DB_USER"),
            password=values.get("EMAP_DB_PASSWORD"),
            host=values.get("EMAP_DB_HOST"),
            path=f"/{values.get('EMAP_DB_NAME') or ''}",
        )

    @validator("CABOODLE_URL")
    def assemble_caboodle_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> str:
        if values.get("ENV") == "dev":
            db_path = Path(__file__).parents[0] / "resources" / "mock.db"
            return f"sqlite:///{db_path}"

        # Construct the MSSQL connection
        db_host = values.get("CABOODLE_DB_HOST")
        db_user = values.get("CABOODLE_DB_USER")
        db_password = values.get("CABOODLE_DB_PASSWORD")
        db_port = values.get("CABOODLE_DB_PORT")
        db_name = values.get("CABOODLE_DB_NAME")
        return (
            f"mssql+pyodbc://{db_user}:{db_password}@{db_host}:{db_port}/"
            + f"{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
        )

    @validator("CLARITY_URL")
    def assemble_clarity_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> str:
        if values.get("ENV") == "dev":
            db_path = Path(__file__).parents[0] / "resources" / "mock.db"
            return f"sqlite:///{db_path}"

        # Construct the MSSQL connection
        db_host = values.get("CLARITY_DB_HOST")
        db_user = values.get("CLARITY_DB_USER")
        db_password = values.get("CLARITY_DB_PASSWORD")
        db_port = values.get("CLARITY_DB_PORT")
        db_name = values.get("CLARITY_DB_NAME")
        return (
            f"mssql+pyodbc://{db_user}:{db_password}@{db_host}:{db_port}/"
            + f"{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
        )

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
        BASE_URL = values.get("BASE_URL")
        BASE_URL_DOCKER_API = values.get("BASE_URL_DOCKER_API")
        PORT_DOCKER_API = values.get("PORT_DOCKER_API")
        PORT_COMMANDLINE_API = values.get("PORT_COMMANDLINE_API")
        if values.get("DOCKER") is True:
            url = f"{BASE_URL_DOCKER_API}:{PORT_DOCKER_API}"
        else:
            url = f"{BASE_URL}:{PORT_COMMANDLINE_API}"
        return url

    @validator("APP_URL")
    def assemble_app_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        :returns:   Base URL for the APP (esp for testing)
        :rtype:     str
        """
        BASE_URL = values.get("BASE_URL")
        BASE_URL_DOCKER_APP = values.get("BASE_URL_DOCKER_APP")
        PORT_DOCKER_APP = values.get("PORT_DOCKER_APP")
        PORT_COMMANDLINE_APP = values.get("PORT_COMMANDLINE_APP")
        if values.get("DOCKER") is True:
            url = f"{BASE_URL_DOCKER_APP}:{PORT_DOCKER_APP}"
        else:
            url = f"{BASE_URL}:{PORT_COMMANDLINE_APP}"
        return url

    @validator("BASEROW_URL", "BASEROW_PUBLIC_URL")
    def assemble_baserow_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        :returns:   Base URL for BASEROW
        :rtype:     str
        """
        BASE_URL = values.get("BASE_URL")
        BASEROW_PORT = values.get("BASEROW_PORT")
        BASE_URL_DOCKER_BASEROW = values.get("BASE_URL_DOCKER_BASEROW")
        PORT_DOCKER_BASEROW = values.get("PORT_DOCKER_BASEROW")

        if values.get("DOCKER") is True:
            url = f"{BASE_URL_DOCKER_BASEROW}:{PORT_DOCKER_BASEROW}"
        else:
            url = f"{BASE_URL}:{BASEROW_PORT}"
        # url = f"{BASE_URL}:{BASEROW_PORT}"
        return url

    class Config:
        case_sensitive = True


settings = Settings()

if __name__ == "__main__":
    for i in settings:
        print(i)
