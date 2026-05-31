"""
Generic repository: every collection gets get / insert / update / delete /
list with pagination, with **no** Mongo leak above this layer.

Why repositories instead of calling Motor directly from routes:
  - Routes stay declarative (HTTP concerns only).
  - Domain logic and DB-shape concerns live in one place per entity.
  - Tests can swap real Mongo for an in-memory fake by injecting a fake repo.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.models.base import MongoModel

T = TypeVar("T", bound=MongoModel)


class BaseRepository(Generic[T]):
    """Subclass and set `collection_name` + `model`."""

    collection_name: str
    model: Type[T]

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        if not self.collection_name:
            raise RuntimeError(f"{type(self).__name__} must define collection_name")
        self.collection: AsyncIOMotorCollection = db[self.collection_name]

    # ---- Read ------------------------------------------------------------
    async def get(self, id: str) -> Optional[T]:
        doc = await self.collection.find_one({"_id": id})
        return self.model.from_mongo(doc)

    async def find_one(self, filter: dict[str, Any]) -> Optional[T]:
        doc = await self.collection.find_one(filter)
        return self.model.from_mongo(doc)

    async def list(
        self,
        *,
        filter: Optional[dict[str, Any]] = None,
        sort: Optional[list[tuple[str, int]]] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[T]:
        cursor = self.collection.find(filter or {})
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return [self.model.from_mongo(doc) async for doc in cursor]  # type: ignore[misc]

    async def count(self, filter: Optional[dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filter or {})

    # ---- Write -----------------------------------------------------------
    async def insert(self, obj: T) -> T:
        await self.collection.insert_one(obj.to_mongo())
        return obj

    async def replace(self, obj: T) -> T:
        """Upsert by _id. Useful for full updates from already-validated models."""
        await self.collection.replace_one({"_id": obj.id}, obj.to_mongo(), upsert=True)
        return obj

    async def update_fields(self, id: str, fields: dict[str, Any]) -> Optional[T]:
        """Partial update using $set. Returns the updated document."""
        doc = await self.collection.find_one_and_update(
            {"_id": id},
            {"$set": fields},
            return_document=True,  # ReturnDocument.AFTER
        )
        return self.model.from_mongo(doc)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": id})
        return result.deleted_count == 1
