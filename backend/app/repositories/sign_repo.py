from __future__ import annotations

import re

from app.models.sign import Sign
from app.repositories.base import BaseRepository


class SignRepository(BaseRepository[Sign]):
    collection_name = "signs"
    model = Sign

    async def search_by_term(self, query: str, *, limit: int = 20) -> list[Sign]:
        # Escape metachars so a stray '(', '[' or '\' in the user's query
        # doesn't blow up Mongo's regex engine with an OperationFailure (500).
        # Partial, case-insensitive matching is preserved.
        return await self.list(
            filter={"portuguese_term": {"$regex": re.escape(query), "$options": "i"}},
            limit=limit,
        )
