"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret_key: str
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 30
    backoffice_public_url: str = "http://localhost:3001"
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    sendgrid_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
