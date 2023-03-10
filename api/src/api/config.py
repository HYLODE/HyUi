from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn, AnyUrl, AnyHttpUrl, SecretStr


class Settings(BaseSettings):
    star_dsn: PostgresDsn
    caboodle_dsn: AnyUrl
    clarity_dsn: AnyUrl

    baserow_url: AnyHttpUrl
    baserow_email: str
    baserow_password: SecretStr
    baserow_application_name: str
    baserow_username: str

    hycastle_url: AnyHttpUrl
    hymind_url: AnyHttpUrl
    towermail_url: AnyHttpUrl

    electives_tap_url: AnyHttpUrl
    emergency_tap_url: AnyHttpUrl

    echo_sql: bool = False

    icu_admission_predictions: bool = False

    slack_log_webhook: SecretStr

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
