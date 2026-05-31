"""
Pydantic base model for MongoDB documents.

Why this exists:
  Mongo's native primary key is `_id`. The original codebase carried BOTH
  a `_id` (auto-generated ObjectId) and a custom `id` (uuid4) on every doc,
  which is a recipe for inconsistent joins. Here we keep a single canonical
  `id` field in Python, and translate to/from Mongo's `_id` at the boundary
  (to_mongo / from_mongo).

  We deliberately do NOT use Pydantic's `alias="_id"` for this, because
  FastAPI serializes response models with `by_alias=True` by default, which
  would leak `_id` into the public JSON contract. Manual translation keeps
  the wire format clean (`id`) while persistence stays Mongo-idiomatic (`_id`).

  Datetimes are stored natively — BSON supports timezone-aware datetimes,
  so no isoformat()/fromisoformat() dance is needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar, Optional, Self, TypeVar

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp. Always prefer this over datetime.utcnow()."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


T = TypeVar("T", bound="MongoModel")


class MongoModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )

    id: str = Field(default_factory=new_id)

    collection_name: ClassVar[str] = ""

    def to_mongo(self) -> dict[str, Any]:
        """Serialize for insertion: rename `id` -> `_id` and coerce Pydantic
        URL types to plain strings (BSON can't encode AnyUrl / HttpUrl)."""
        data = self.model_dump()
        data["_id"] = data.pop("id")
        return _bsonify(data)

    @classmethod
    def from_mongo(cls, doc: Optional[dict[str, Any]]) -> Optional[Self]:
        if doc is None:
            return None
        data = dict(doc)
        if "_id" in data:
            data["id"] = data.pop("_id")
        return cls.model_validate(data)


class TimestampedModel(MongoModel):
    """Adds created_at / updated_at. Most domain entities want this."""

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()


def _bsonify(value: Any) -> Any:
    """Walk a dict/list tree and coerce Pydantic URL types to str.

    BSON natively encodes datetime, UUID strings, ints, floats, bool, str.
    It does NOT encode pydantic.AnyUrl. Conversion at this single chokepoint
    means every domain model gets the fix for free.
    """
    if isinstance(value, AnyUrl):
        return str(value)
    if isinstance(value, dict):
        return {k: _bsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_bsonify(v) for v in value]
    return value
