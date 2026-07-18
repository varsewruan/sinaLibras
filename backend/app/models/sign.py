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
    # Signs recorded on video ship two encodes: video_url is H.264/MP4 with the
    # background flattened (Safari/iOS), video_webm_url is VP9 with a live alpha
    # channel (Chrome/Firefox/Edge). No single codec gives transparency
    # everywhere — see scripts/build_sign_videos.py. Both are None for signs
    # that only have an SVG placeholder, which is still most of the catalog.
    video_webm_url: Optional[str] = None
    poster_url: Optional[str] = None
    # Optional accessibility text describing the gesture for screen-reader users.
    text_description: str = Field(default="", max_length=1000)
