"""Profile mutations that aren't authentication concerns.

Today that's just the avatar. Kept separate from AuthService so the auth
surface stays about credentials and tokens.
"""

from __future__ import annotations

from app.models.base import utc_now
from app.models.user import User
from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self, *, users: UserRepository) -> None:
        self.users = users

    async def update_avatar(self, *, user: User, avatar: str) -> User:
        """Persist a new avatar preset id.

        The id was already validated against the allowlist by the request DTO,
        so anything reaching here is safe to store.
        """
        updated = await self.users.update_fields(
            user.id, {"avatar": avatar, "updated_at": utc_now()}
        )
        # update_fields returns the post-update document; fall back to a
        # locally-rebuilt one if Mongo returned nothing (shouldn't happen).
        return updated or user.model_copy(update={"avatar": avatar})
