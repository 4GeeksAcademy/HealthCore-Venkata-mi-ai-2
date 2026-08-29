"""User resource routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import hash_password
from app.deps.auth import get_current_user
from app.models.users import RegisterRequest, UserResponse, UserRole, UserUpdateRequest, UserWithProfileResponse
from app.stores import auth_store

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserWithProfileResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=UserWithProfileResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_user(payload: RegisterRequest) -> UserWithProfileResponse:
    try:
        created = auth_store.create_user_with_profile(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    return UserWithProfileResponse(**created)


@router.get("", response_model=list[UserResponse])
@router.get("/", response_model=list[UserResponse], include_in_schema=False)
def list_users(_: dict = Depends(get_current_user)) -> list[UserResponse]:
    return [UserResponse(**user) for user in auth_store.list_users()]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, _: dict = Depends(get_current_user)) -> UserResponse:
    found = auth_store.get_user_by_id(user_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**found)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    is_admin = current_user["role"] == UserRole.admin.value
    is_owner = current_user["id"] == user_id

    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if payload.role is not None and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change role")

    hashed_password = hash_password(payload.password) if payload.password is not None else None

    try:
        updated = auth_store.update_user(
            user_id,
            email=str(payload.email) if payload.email is not None else None,
            hashed_password=hashed_password,
            is_active=payload.is_active,
            role=payload.role.value if payload.role is not None else None,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(**updated)


@router.delete("/{user_id}", response_model=dict[str, bool])
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)) -> dict[str, bool]:
    is_admin = current_user["role"] == UserRole.admin.value
    is_owner = current_user["id"] == user_id

    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    removed = auth_store.delete_user_and_profile(user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"ok": True}
