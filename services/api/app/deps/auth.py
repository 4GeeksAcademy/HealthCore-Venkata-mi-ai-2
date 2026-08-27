"""Auth dependency helpers for protected routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.stores import auth_store

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise ValueError("Missing subject")
        user_id = int(raw_sub)
    except (ValueError, TypeError):
        raise unauthorized

    user = auth_store.get_user_by_id(user_id)
    if user is None or not user.get("is_active", False):
        raise unauthorized

    return user
