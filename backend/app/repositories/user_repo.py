from __future__ import annotations

from typing import Optional

from pymongo import ASCENDING, DESCENDING

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    collection_name = "users"
    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        # Emails are normalized to lowercase by the auth DTO validators
        # before they ever reach this layer, so an exact match is both
        # sufficient and safer than a regex (avoids metachar injection
        # like '+' or '.' inside addresses).
        return await self.find_one({"email": email.strip().lower()})

    async def top_by_xp(self, *, limit: int = 20) -> list[User]:
        """Leaderboard page. Ties broken by signup date (older account first)."""
        return await self.list(
            sort=[("xp", DESCENDING), ("created_at", ASCENDING)],
            limit=limit,
        )

    async def count_with_more_xp(self, xp: int) -> int:
        """How many users are strictly ahead — used to place a user's own rank
        without paging through the whole collection (standard competition
        ranking: everyone tied on XP shares the same rank)."""
        return await self.count({"xp": {"$gt": xp}})
