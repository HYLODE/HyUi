from functools import lru_cache

from pydantic import BaseSettings, SecretStr, HttpUrl


class Settings(BaseSettings):
    username: str
    password: SecretStr
    secret_key: SecretStr

    # The port to use when running in development mode.
    development_port: str = "8000"

    api_url: HttpUrl

    class Config:
        env_prefix = "web_"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
