"""Status check — kept for backwards compatibility with the original template.

It's a useful smoke-test endpoint: clients POST a name and we echo it back
with a timestamp. Will be removed once a richer health/observability surface
exists.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field

from app.models.base import TimestampedModel, utc_now


class StatusCheck(TimestampedModel):
    collection_name: ClassVar[str] = "status_checks"

    client_name: str = Field(..., min_length=1, max_length=200)
    timestamp: datetime = Field(default_factory=utc_now)


class StatusCheckCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=200)
