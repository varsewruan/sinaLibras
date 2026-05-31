from __future__ import annotations

from typing import Optional

from app.models.progress import Progress
from app.repositories.base import BaseRepository


class ProgressRepository(BaseRepository[Progress]):
    collection_name = "progress"
    model = Progress

    async def get_for_user_lesson(self, user_id: str, lesson_id: str) -> Optional[Progress]:
        return await self.find_one({"user_id": user_id, "lesson_id": lesson_id})

    async def list_for_user(self, user_id: str, *, limit: int = 100) -> list[Progress]:
        return await self.list(filter={"user_id": user_id}, limit=limit)
