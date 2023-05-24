from functools import lru_cache

from pydantic import BaseSettings, EmailStr, SecretStr, AnyHttpUrl, PostgresDsn, AnyUrl


class BaserowSettings(BaseSettings):
    email: EmailStr
    username: str
    password: SecretStr

    public_url: AnyHttpUrl

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "baserow_"
        frozen = True


@lru_cache()
def get_baserow_settings() -> BaserowSettings:
    return BaserowSettings()


class DatabaseSettings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "db_"
        frozen = True


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    return DatabaseSettings()
