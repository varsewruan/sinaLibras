from __future__ import annotations

from typing import Optional

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
