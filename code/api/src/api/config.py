from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, AnyUrl, HttpUrl


class Settings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl
    clarity_dsn: AnyUrl

    baserow_url: HttpUrl
    baserow_read_write_token: str

    class Config:
        env_prefix = "api_"


@lru_cache()
def get_settings() -> Settings:
    """
    This function allows Settings to be lazily instantiated so that testing
    can be done without having to set environment variables.
    """
    return Settings()
