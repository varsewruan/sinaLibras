from __future__ import annotations

from app.models.phase import Phase
from app.repositories.base import BaseRepository


class PhaseRepository(BaseRepository[Phase]):
    collection_name = "phases"
    model = Phase

    async def list_ordered(self, *, limit: int = 100) -> list[Phase]:
        return await self.list(sort=[("order", 1)], limit=limit)
