from __future__ import annotations

from app.models.lesson import Lesson
from app.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    collection_name = "lessons"
    model = Lesson

    async def list_by_phase(self, phase_id: str, *, limit: int = 100) -> list[Lesson]:
        return await self.list(
            filter={"phase_id": phase_id},
            sort=[("order", 1)],
            limit=limit,
        )
