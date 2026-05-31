"""A Lesson is a teachable unit inside a Phase, made of one or more Signs."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.models.base import TimestampedModel


class Lesson(TimestampedModel):
    collection_name: ClassVar[str] = "lessons"

    phase_id: str = Field(..., min_length=1, description="FK -> phases._id")
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    order: int = Field(..., ge=1, description="Position inside the phase")
    sign_ids: list[str] = Field(default_factory=list, description="FK -> signs._id")
    xp_reward: int = Field(default=10, ge=0)
