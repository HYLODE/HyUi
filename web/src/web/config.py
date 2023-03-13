from functools import lru_cache

from pydantic import BaseSettings, SecretStr, AnyHttpUrl


class Settings(BaseSettings):
    username: str
    password: SecretStr
    secret_key: SecretStr

    # The port to use when running in development mode.
    port: str

    api_url: AnyHttpUrl
    baserow_public_url: AnyHttpUrl

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "web_"
        frozen = True  # So Settings can be hashable and cachable


@lru_cache()
def get_settings() -> Settings:
    return Settings()
