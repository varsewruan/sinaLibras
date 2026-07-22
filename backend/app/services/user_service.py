"""Profile mutations that aren't authentication concerns.

Today that's just the avatar. Kept separate from AuthService so the auth
surface stays about credentials and tokens.
"""

from __future__ import annotations

from app.models.base import utc_now
from app.models.shop import get_item, is_owned
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.shop_service import ShopError


class UserService:
    def __init__(self, *, users: UserRepository) -> None:
        self.users = users

    async def update_avatar(self, *, user: User, avatar: str) -> User:
        """Persist a new avatar preset id.

        The DTO already checked the id against the allowlist, but that only
        says the avatar EXISTS. Since avatars became purchasable, existing and
        being allowed to wear it are different questions — without this check
        this endpoint is a free bypass around the shop.
        """
        item = get_item(avatar)
        if item is not None and not is_owned(item, user.owned_items):
            raise ShopError("not_owned", "Compre este avatar antes de usá-lo.")

        updated = await self.users.update_fields(
            user.id, {"avatar": avatar, "updated_at": utc_now()}
        )
        # update_fields returns the post-update document; fall back to a
        # locally-rebuilt one if Mongo returned nothing (shouldn't happen).
        return updated or user.model_copy(update={"avatar": avatar})
