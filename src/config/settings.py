# ./src/api/settings_src.py
# project wide settings are loaded via ./.envrc and ./.secrets
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    ENV: str
    UDS_HOST: str
    UDS_USER: str
    UDS_PWD: str
    UDS_DB: str

    DB_URL: Optional[str]

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
            db_path = Path(__file__).resolve().parents[1].absolute() / "data" / "mock"
            db_url = f"sqlite:///{db_path.as_posix()}/mock.db"
            return db_url
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("UDS_USER"),
            password=values.get("UDS_PWD"),
            host=values.get("UDS_HOST"),
            path=f"/{values.get('UDS_DB') or ''}",
        )

    class Config:
        case_sensitive = True


settings = Settings()
# print(settings.dict())
