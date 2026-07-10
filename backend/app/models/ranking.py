"""Read-only DTOs for the /ranking endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.user import User


class RankingEntry(BaseModel):
    """One row of the leaderboard. Deliberately omits email — a leaderboard
    is visible to every logged-in user, and addresses aren't theirs to see."""

    rank: int
    id: str
    name: str
    avatar: str
    xp: int
    streak: int
    is_me: bool = False

    @classmethod
    def from_user(cls, user: User, *, rank: int, is_me: bool = False) -> "RankingEntry":
        return cls(
            rank=rank,
            id=user.id,
            name=user.name,
            avatar=user.avatar,
            xp=user.xp,
            streak=user.streak.current,
            is_me=is_me,
        )


class RankingResponse(BaseModel):
    entries: list[RankingEntry]
    # The caller's own row. Present even when they fall outside the top-N, so
    # the UI can pin "your position" below the list. None only if unauthenticated.
    me: Optional[RankingEntry] = None
