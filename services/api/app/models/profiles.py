"""Pydantic models for profile endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
