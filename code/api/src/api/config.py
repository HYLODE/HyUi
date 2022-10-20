from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, AnyUrl, HttpUrl


class Settings(BaseSettings):
    star_dsn: PostgresDsn | None
    caboodle_dsn: AnyUrl | None
    clarity_dsn: AnyUrl | None

    baserow_url: HttpUrl | None
    baserow_read_write_token: str | None

    # TODO: Remove this when refactoring is done.
    env = "dev"

    class Config:
        env_prefix = "api_"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
