"""Profile resource routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import get_current_user
from app.models.profiles import ProfileUpdateRequest
from app.models.users import ProfileResponse
from app.stores import auth_store

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    profile = auth_store.get_profile_by_user_id(current_user["id"])
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse(**profile)


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    updated = auth_store.update_profile_for_user(
        current_user["id"],
        name=payload.name,
        phone=payload.phone,
        address=payload.address,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse(**updated)
