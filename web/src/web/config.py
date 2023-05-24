from functools import lru_cache

from pydantic import BaseSettings, SecretStr, AnyHttpUrl, AnyUrl, Field


class Settings(BaseSettings):
    debug: int = Field(..., env="DEBUG")  # 0 = False, 1 = True
    username: str
    password: SecretStr
    secret_key: SecretStr

    # The port to use when running in development mode.
    development_port: str = "8000"

    api_url: AnyHttpUrl
    baserow_public_url: AnyHttpUrl
    celery_dash_broker_url: AnyUrl
    celery_dash_result_backend: AnyUrl
    redis_cache: AnyUrl

    hyui_user: str
    hyui_password: SecretStr

    slack_log_webhook: SecretStr

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "web_"
        frozen = True  # So Settings can be hashable and cachable


@lru_cache()
def get_settings() -> Settings:
    return Settings()
