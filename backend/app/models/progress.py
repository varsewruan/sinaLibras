"""Per-user, per-lesson progress record + DTOs for the /progress/* endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from app.models.base import TimestampedModel
from app.models.user import StreakState, UserPublic


class Progress(TimestampedModel):
    collection_name: ClassVar[str] = "progress"

    user_id: str = Field(..., min_length=1, description="FK -> users._id")
    lesson_id: str = Field(..., min_length=1, description="FK -> lessons._id")
    score: int = Field(default=0, ge=0, le=100)
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    attempts: int = Field(default=0, ge=0)


class CompleteLessonRequest(BaseModel):
    lesson_id: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=100)


class CompleteLessonResponse(BaseModel):
    """Returned after POST /progress/complete-lesson — everything the UI
    needs to flash a result screen without a second round-trip."""
    progress: Progress
    user: UserPublic
    awarded_xp: int
    passed: bool
    streak: StreakState
