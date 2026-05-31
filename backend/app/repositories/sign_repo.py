from __future__ import annotations

from app.models.sign import Sign
from app.repositories.base import BaseRepository


class SignRepository(BaseRepository[Sign]):
    collection_name = "signs"
    model = Sign

    async def search_by_term(self, query: str, *, limit: int = 20) -> list[Sign]:
        return await self.list(
            filter={"portuguese_term": {"$regex": query, "$options": "i"}},
            limit=limit,
        )
