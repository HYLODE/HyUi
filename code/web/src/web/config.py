from functools import lru_cache

from pydantic import BaseSettings, SecretStr, AnyHttpUrl


class Settings(BaseSettings):
    username: str
    password: SecretStr
    secret_key: SecretStr

    # The port to use when running in development mode.
    development_port: str = "8001"

    api_url: AnyHttpUrl

    class Config:
        env_prefix = "web_"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
