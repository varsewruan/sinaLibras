"""A learning Phase groups Lessons in a global order (1, 2, 3, ...)."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.models.base import TimestampedModel


class Phase(TimestampedModel):
    collection_name: ClassVar[str] = "phases"

    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    order: int = Field(..., ge=1, description="Position in the learning path")
