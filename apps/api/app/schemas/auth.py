"""Auth request/response schemas (Pydantic v2)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole

RegisterRole = Literal["buyer", "seller"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: RegisterRole
    company_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    full_name: str
    company_name: str | None = None
    phone: str | None = None
    is_suspended: bool = False
    created_at: datetime | None = None


class AccessTokenResponse(BaseModel):
    """Access token only — refresh token is HttpOnly cookie, never in body."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
