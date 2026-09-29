"""Application settings loaded from environment variables."""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _fernet_from_jwt(jwt_secret: str) -> Fernet:
    digest = hashlib.sha256(jwt_secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def decode_app_secret(value: str, jwt_secret: str) -> str:
    """Decode enc:v1: (Fernet) or b64: payloads. Plain values pass through."""
    if value.startswith("enc:v1:"):
        try:
            return _fernet_from_jwt(jwt_secret).decrypt(value[7:].encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError) as exc:
            raise ValueError("Unable to decrypt SUPABASE_DATABASE_URL with JWT_SECRET_KEY") from exc
    if value.startswith("b64:"):
        try:
            return base64.urlsafe_b64decode(value[4:].encode("ascii")).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Unable to decode SUPABASE_DATABASE_URL b64 payload") from exc
    return value


class Settings(BaseSettings):
    jwt_secret_key: str
    database_url: str = "sqlite://"
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 30
    backoffice_public_url: str = "http://localhost:3001"
    telemetry_endpoint: str = "http://localhost:3001/hc-api/telemetry/events"
    inventory_backend: str = "tinydb"
    supabase_database_url: str | None = Field(default=None)
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    sendgrid_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _decode_supabase_url(self) -> Settings:
        backend = self.inventory_backend.strip().lower()
        if backend not in {"tinydb", "supabase"}:
            raise ValueError("INVENTORY_BACKEND must be tinydb or supabase")
        object.__setattr__(self, "inventory_backend", backend)
        if self.supabase_database_url:
            object.__setattr__(
                self,
                "supabase_database_url",
                decode_app_secret(self.supabase_database_url, self.jwt_secret_key),
            )
        if backend == "supabase" and not (self.supabase_database_url or self.database_url):
            raise ValueError("SUPABASE_DATABASE_URL or DATABASE_URL is required when INVENTORY_BACKEND=supabase")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
