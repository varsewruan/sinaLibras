"""A Sign is the atomic content unit: a single gesture in Libras."""

from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import Field

from app.models.base import TimestampedModel


class Sign(TimestampedModel):
    collection_name: ClassVar[str] = "signs"

    portuguese_term: str = Field(..., min_length=1, max_length=120)
    libras_description: str = Field(default="", max_length=1000)
    # video_url / thumbnail_url stay as plain strings because the catalog
    # mixes absolute CDN URLs with backend-relative paths like "/signs/ola.svg".
    # Pydantic's HttpUrl rejects the latter; we trust the seed pipeline +
    # frontend resolver to normalize at render time.
    video_url: Optional[str] = Field(default=None, description="Demo video of the sign")
    thumbnail_url: Optional[str] = None
    # Optional accessibility text describing the gesture for screen-reader users.
    text_description: str = Field(default="", max_length=1000)
