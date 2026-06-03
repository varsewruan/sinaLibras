"""
Composed read-only DTOs for the /learning/* endpoints.

These are *views* over the underlying entities — they don't get persisted.
Keeping them separate from the domain models lets us change the wire
contract without touching storage shape, and vice versa.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.models.sign import Sign


class LessonSummary(BaseModel):
    """Lesson as shown inside a phase card on the Path screen."""
    id: str
    title: str
    description: str = ""
    order: int
    xp_reward: int
    sign_count: int = Field(..., ge=0)
    completed: bool = False
    score: Optional[int] = None  # 0-100 if attempted; None otherwise


class PhaseWithLessons(BaseModel):
    id: str
    title: str
    description: str = ""
    order: int
    lessons: list[LessonSummary]


class SignView(BaseModel):
    """Public sign view served by GET /lessons/:id and the dictionary."""
    id: str
    portuguese_term: str
    libras_description: str = ""
    text_description: str = ""
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None

    @classmethod
    def from_sign(cls, sign: "Sign") -> "SignView":
        return cls(
            id=sign.id,
            portuguese_term=sign.portuguese_term,
            libras_description=sign.libras_description,
            text_description=sign.text_description,
            thumbnail_url=str(sign.thumbnail_url) if sign.thumbnail_url else None,
            video_url=str(sign.video_url) if sign.video_url else None,
        )


class LessonDetail(BaseModel):
    id: str
    phase_id: str
    title: str
    description: str = ""
    order: int
    xp_reward: int
    signs: list[SignView]
