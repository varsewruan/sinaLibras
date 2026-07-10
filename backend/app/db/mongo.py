"""
Async MongoDB client lifecycle and index management.

We hold the client in module-level state because Motor pools connections
internally — re-creating it per request would defeat the pool. The client
is opened in the FastAPI lifespan (`app.main.lifespan`) and closed at shutdown.

`ensure_indexes()` runs once at startup and is idempotent: Mongo's
`create_index` is a no-op when the index already exists with the same spec.
"""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo(settings: Settings) -> AsyncIOMotorDatabase:
    """Open the client and verify connectivity with a ping."""
    global _client, _db
    if _client is not None:
        return _db  # type: ignore[return-value]

    logger.info("mongo_connecting", db=settings.DB_NAME)
    _client = AsyncIOMotorClient(
        settings.MONGO_URL,
        serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        maxPoolSize=settings.MONGO_MAX_POOL_SIZE,
        uuidRepresentation="standard",
        # tz_aware=True makes datetimes loaded from Mongo timezone-aware
        # (UTC). Without this, BSON dates come back naive and Pydantic
        # treats them as local time. Always-on UTC is the safer default.
        tz_aware=True,
    )
    # Fail fast if Mongo is unreachable — better than a 500 on the first request.
    await _client.admin.command("ping")
    _db = _client[settings.DB_NAME]
    logger.info("mongo_connected", db=settings.DB_NAME)
    return _db


async def close_mongo_connection() -> None:
    global _client, _db
    if _client is not None:
        logger.info("mongo_disconnecting")
        _client.close()
        _client = None
        _db = None


def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency. Raises if the lifespan didn't run (e.g. misconfigured tests)."""
    if _db is None:
        raise RuntimeError(
            "Mongo is not initialized. Did the FastAPI lifespan run? "
            "In tests, call connect_to_mongo(test_settings) before issuing requests."
        )
    return _db


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create all domain indexes. Safe to call repeatedly."""
    logger.info("mongo_ensuring_indexes")

    # users: email is the natural unique key for login
    await db.users.create_index("email", unique=True, name="uniq_users_email")

    # users: leaderboard reads the top-N by XP. created_at breaks ties so the
    # order is stable across requests (earlier account wins an XP tie).
    await db.users.create_index(
        [("xp", DESCENDING), ("created_at", ASCENDING)],
        name="idx_users_xp_desc",
    )

    # progress: a user can only complete a given lesson once (most recent attempt wins)
    await db.progress.create_index(
        [("user_id", ASCENDING), ("lesson_id", ASCENDING)],
        unique=True,
        name="uniq_progress_user_lesson",
    )
    await db.progress.create_index("user_id", name="idx_progress_user")

    # lessons: ordered inside a phase
    await db.lessons.create_index(
        [("phase_id", ASCENDING), ("order", ASCENDING)],
        name="idx_lessons_phase_order",
    )

    # phases: global order is unique (no two phases share position #1)
    await db.phases.create_index("order", unique=True, name="uniq_phases_order")

    # signs: lookup by Portuguese term (UI search)
    await db.signs.create_index("portuguese_term", name="idx_signs_pt_term")

    logger.info("mongo_indexes_ready")
