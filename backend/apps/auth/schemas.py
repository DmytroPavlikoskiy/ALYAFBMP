from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str | None = None
    phone: str | None = None
    tg_chat_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tg_chat_id: int | None = None


class TokenResponse(BaseModel):
    access: str
    refresh: str


class RegisterResponse(BaseModel):
    user_id: UUID
