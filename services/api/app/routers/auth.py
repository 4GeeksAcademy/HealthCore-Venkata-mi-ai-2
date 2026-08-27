"""Authentication routes."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.deps.auth import get_current_user
from app.models.users import (
    AccessTokenResponse,
    AuthMeResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
)
from app.stores import auth_store

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _dispatch_reset_email(*, to_email: str, reset_link: str) -> None:
    # Demo mode: do not send real outbound email requests.
    logger.info("Demo password reset link for %s: %s", to_email, reset_link)


@router.post("/login", response_model=AccessTokenResponse)
def login(payload: LoginRequest) -> AccessTokenResponse:
    user = auth_store.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token = create_access_token(subject=str(user["id"]), role=user["role"])
    return AccessTokenResponse(access_token=access_token)


@router.get("/me", response_model=AuthMeResponse)
def auth_me(current_user: dict = Depends(get_current_user)) -> AuthMeResponse:
    profile = auth_store.get_profile_by_user_id(current_user["id"])
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return AuthMeResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        profile=profile,
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest) -> MessageResponse:
    message = "If that address is registered, you'll receive a link shortly."
    user = auth_store.get_user_by_email(payload.email)
    if user is None:
        return MessageResponse(message=message)

    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.reset_token_expire_minutes
    )

    auth_store.create_reset_token(
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at.replace(microsecond=0).isoformat(),
    )

    reset_link = f"{settings.backoffice_public_url}/reset-password?token={raw_token}"
    _dispatch_reset_email(to_email=user["email"], reset_link=reset_link)

    return MessageResponse(message=message)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    token_hash = _hash_reset_token(payload.token)
    user_id = auth_store.consume_reset_token(token_hash)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    updated = auth_store.update_user(
        user_id,
        hashed_password=hash_password(payload.new_password),
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    return MessageResponse(message="Password reset successful")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    if not verify_password(payload.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    auth_store.update_user(
        current_user["id"],
        hashed_password=hash_password(payload.new_password),
    )
    return MessageResponse(message="Password changed successfully")
