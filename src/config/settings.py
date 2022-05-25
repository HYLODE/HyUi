# ./src/api/settings_src.py
# project wide settings are loaded via ./.envrc and ./.secrets
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator

URL_DOCKER_TRUE = "http://api:8094/results/"
URL_DOCKER_FALSE = "http://localhost:8094/results/"


class Settings(BaseSettings):
    ENV: str
    DOCKERNETWORK = 0
    UDS_HOST: str
    UDS_USER: str
    UDS_PWD: str
    UDS_DB: str

    DB_URL: Optional[str]
    DB_POSTGRES_SCHEMA = "star"
    BACKEND_URL: Optional[str]

    @validator("ENV", pre=True)
    def environment_choice_is_valid(cls, v):
        # b/c when read from .secrets a \r (carriage return) is appended
        v = v.rstrip()
        if v not in ["dev", "prod"]:
            raise ValueError(f"ENV environment variable ({v}) must be one of dev/prod")
        return v

    @validator("DB_URL")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if values.get("ENV") == "dev":
            db_path = Path(__file__).resolve().parents[1].absolute() / "mock"
            db_url = f"sqlite:///{db_path.as_posix()}/mock.db"
            return db_url
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            user=values.get("UDS_USER"),
            password=values.get("UDS_PWD"),
            host=values.get("UDS_HOST"),
            path=f"/{values.get('UDS_DB') or ''}",
        )

    @validator("BACKEND_URL")
    def assemble_api_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """
        Defines API URL based on whether working in conda environment, or
        from within the docker-compose network
        """
        if values.get("DOCKERNETWORK") == 1:
            api_url = URL_DOCKER_TRUE
        else:
            api_url = URL_DOCKER_FALSE
        return api_url

    class Config:
        case_sensitive = True


settings = Settings()
