from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, AnyUrl, AnyHttpUrl


class Settings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl
    clarity_dsn: AnyUrl

    baserow_url: AnyHttpUrl
    baserow_read_write_token: str
    baserow_beds_table_id: int

    hycastle_url: AnyHttpUrl
    hymind_url: AnyHttpUrl
    towermail_url: AnyHttpUrl

    class Config:
        env_prefix = "api_"
        frozen = True  # So Settings can be hashable and cachable


@lru_cache()
def get_settings() -> Settings:
    """
    This function allows Settings to be lazily instantiated so that testing
    can be done without having to set environment variables.
    """
    return Settings()
