"""Pydantic models for authentication and user resources."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""
    phone: str = ""
    address: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: str


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str = ""
    phone: str = ""
    address: str = ""


class UserWithProfileResponse(BaseModel):
    user: UserResponse
    profile: ProfileResponse


class AuthMeResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    profile: ProfileResponse


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    is_active: bool | None = None
    role: UserRole | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class MessageResponse(BaseModel):
    message: str
