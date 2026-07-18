"""DTOs for the /auth/* endpoints.

These are wire-format only — they never touch Mongo directly. The service
layer maps them to/from the User domain model.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserPublic


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("password")
    @classmethod
    def _disallow_obvious(cls, v: str) -> str:
        # NIST 800-63B: length matters more than complexity. We reject only
        # the bottom of the barrel; we don't enforce upper/symbol/digit rules.
        if v.lower() in {"password", "12345678", "qwerty12", "11111111", "00000000"}:
            raise ValueError("Esta senha é muito comum. Escolha outra.")
        return v

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponse(BaseModel):
    """Body returned on login / register / refresh.

    The tokens themselves go in httpOnly cookies, not in this body — including
    them here would defeat the whole point of httpOnly. We return only the
    safe public user view so the SPA can hydrate its AuthContext.
    """

    user: UserPublic
