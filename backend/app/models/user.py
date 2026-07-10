"""User domain model.

The auth fields (hashed_password) live here, but the *logic* of hashing,
verifying and issuing tokens belongs in app.core.security.
This model is just the storage shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.base import TimestampedModel, utc_now


# Avatar presets. Stored as an id string; the SPA maps each id to a gradient
# + emoji (frontend/src/lib/avatars.js). Keep the two lists in sync — the
# backend is the allowlist, so an id missing here can never be persisted.
DEFAULT_AVATAR = "dummy"

AVATAR_IDS: frozenset[str] = frozenset(
    {
        "dummy", "fox", "cat", "panda", "owl", "frog",
        "robot", "hero", "star", "alien", "unicorn", "ninja",
    }
)


class StreakState(BaseModel):
    """Gamification streak — embedded, not a separate collection.

    A streak is meaningless without a user, and we never query streaks
    independently of one. Embedding keeps reads atomic.
    """

    current: int = Field(default=0, ge=0)
    longest: int = Field(default=0, ge=0)
    last_activity_at: Optional[datetime] = None


class User(TimestampedModel):
    collection_name: ClassVar[str] = "users"

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=120)
    hashed_password: str = Field(..., min_length=1)

    # Users created before avatars existed simply get the default on read.
    avatar: str = Field(default=DEFAULT_AVATAR, max_length=32)

    xp: int = Field(default=0, ge=0)
    streak: StreakState = Field(default_factory=StreakState)

    # Bumped on logout or password change. The JWT carries the version it was
    # issued under; if the user's current version is higher, the token is
    # rejected. Cheap stateless revocation, no denylist needed.
    token_version: int = Field(default=0, ge=0)


class UserPublic(BaseModel):
    """Safe representation: never leak hashed_password to the client."""

    id: str
    email: EmailStr
    name: str
    avatar: str
    xp: int
    streak: StreakState
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar=user.avatar,
            xp=user.xp,
            streak=user.streak,
            created_at=user.created_at,
        )


class UpdateAvatarRequest(BaseModel):
    """Body of PATCH /users/me — the only profile field editable today."""

    avatar: str = Field(..., max_length=32)

    @field_validator("avatar")
    @classmethod
    def _known_preset(cls, v: str) -> str:
        if v not in AVATAR_IDS:
            raise ValueError(f"unknown avatar preset: {v!r}")
        return v
