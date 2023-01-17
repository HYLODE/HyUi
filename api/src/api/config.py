from functools import lru_cache
from pydantic import AnyHttpUrl, AnyUrl, BaseSettings, PostgresDsn, SecretStr


class Settings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl
    clarity_dsn: AnyUrl

    # Used for baserow admin tasks
    baserow_url: AnyHttpUrl
    baserow_email: str
    baserow_password: SecretStr

    hycastle_url: AnyHttpUrl
    hymind_url: AnyHttpUrl
    towermail_url: AnyHttpUrl

    echo_sql: bool = False

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


class BaserowSettings(BaseSettings):
    """Used for database read/write"""

    read_write_token: SecretStr

    application_id: int

    table_departments: int
    table_rooms: int
    table_beds: int
    table_discharge_statuses: int

    class Config:
        env_file = ".env.baserow"
        env_file_encoding = "utf-8"
        # The prefix below scopes the .env variables.
        env_prefix = "baserow_"
        frozen = True  # So Settings can be hashable and cachable


@lru_cache()
def get_settings_baserow() -> BaserowSettings:
    """
    This function allows Settings to be lazily instantiated so that testing
    can be done without having to set environment variables.
    """
    return BaserowSettings()
