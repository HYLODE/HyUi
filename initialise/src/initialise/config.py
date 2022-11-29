from functools import lru_cache

from pydantic import BaseSettings, EmailStr, SecretStr, AnyHttpUrl


class Settings(BaseSettings):

    baserow_email: EmailStr
    baserow_username: str
    baserow_password: SecretStr

    baserow_base_url: AnyHttpUrl = "http://baserow:80"

    class Config:
        # The prefix below scopes the .env variables.
        env_prefix = "INIT_"
        frozen = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
