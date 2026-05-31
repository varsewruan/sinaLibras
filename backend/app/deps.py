"""FastAPI dependencies.

Two concerns live here:
  1. Wiring: turn `db` into a repository instance for each entity.
  2. Authentication: extract the current User from the access_token cookie.

Keep them thin — no business logic.
"""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.core.security import TokenError, decode_token
from app.db.mongo import get_db
from app.models.user import User
from app.repositories.lesson_repo import LessonRepository
from app.repositories.phase_repo import PhaseRepository
from app.repositories.progress_repo import ProgressRepository
from app.repositories.sign_repo import SignRepository
from app.repositories.status_repo import StatusRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.learning_service import LearningService
from app.services.progress_service import ProgressService


# ---------------- Repositories ----------------------------------------------

def get_user_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_phase_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> PhaseRepository:
    return PhaseRepository(db)


def get_lesson_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> LessonRepository:
    return LessonRepository(db)


def get_sign_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> SignRepository:
    return SignRepository(db)


def get_progress_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProgressRepository:
    return ProgressRepository(db)


def get_status_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> StatusRepository:
    return StatusRepository(db)


# ---------------- Services --------------------------------------------------

def get_auth_service(
    users: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(settings=settings, users=users)


def get_learning_service(
    phases: PhaseRepository = Depends(get_phase_repo),
    lessons: LessonRepository = Depends(get_lesson_repo),
    signs: SignRepository = Depends(get_sign_repo),
    progress: ProgressRepository = Depends(get_progress_repo),
) -> LearningService:
    return LearningService(phases=phases, lessons=lessons, signs=signs, progress=progress)


def get_progress_service(
    users: UserRepository = Depends(get_user_repo),
    lessons: LessonRepository = Depends(get_lesson_repo),
    progress: ProgressRepository = Depends(get_progress_repo),
) -> ProgressService:
    return ProgressService(users=users, lessons=lessons, progress=progress)


# ---------------- Auth ------------------------------------------------------

ACCESS_COOKIE = "access_token"


def _unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Cookie"},
    )


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
    users: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings),
) -> User:
    if not access_token:
        raise _unauthorized("missing_access_token", "no access token cookie")
    try:
        payload = decode_token(settings=settings, token=access_token, expected_type="access")
    except TokenError as exc:
        raise _unauthorized("invalid_access_token", str(exc))

    user = await users.get(payload["sub"])
    if user is None:
        raise _unauthorized("user_not_found", "user no longer exists")

    if payload["tv"] != user.token_version:
        raise _unauthorized("token_revoked", "this token was revoked")

    return user


async def optional_current_user(
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
    users: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """For endpoints that have a public + a logged-in mode (e.g. /lessons)."""
    if not access_token:
        return None
    try:
        return await get_current_user(
            access_token=access_token, users=users, settings=settings
        )
    except HTTPException:
        return None
