from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, AnyUrl, AnyHttpUrl, SecretStr


class Settings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl
    clarity_dsn: AnyUrl

    baserow_url: AnyHttpUrl
    baserow_email: str
    baserow_password: SecretStr
    baserow_read_write_token: SecretStr

    hycastle_url: AnyHttpUrl
    hymind_url: AnyHttpUrl
    towermail_url: AnyHttpUrl

    echo_sql: bool = False

    baserow_application_id: int
    baserow_table_departments: int
    baserow_table_rooms: int
    baserow_table_beds: int
    baserow_table_discharge_statuses: int

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "api_"
        frozen = True  # So Settings can be hashable and cachable


@lru_cache()
def get_settings() -> Settings:
    """
    This function allows Settings to be lazily instantiated so that testing
    can be done without having to set environment variables.
    """
    return Settings()
