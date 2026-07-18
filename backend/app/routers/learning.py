"""Public-readable learning content: phases, lessons, signs."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_learning_service, get_sign_repo, optional_current_user
from app.models.learning import LessonDetail, PhaseWithLessons, SignView
from app.models.user import User
from app.repositories.sign_repo import SignRepository
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get(
    "/phases",
    response_model=list[PhaseWithLessons],
    summary="List phases with their lessons (and user progress, if logged in)",
)
async def list_phases(
    user: Optional[User] = Depends(optional_current_user),
    service: LearningService = Depends(get_learning_service),
) -> list[PhaseWithLessons]:
    return await service.list_phases_with_lessons(user_id=user.id if user else None)


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetail,
    summary="Lesson with its signs",
)
async def get_lesson(
    lesson_id: str,
    service: LearningService = Depends(get_learning_service),
) -> LessonDetail:
    detail = await service.get_lesson_detail(lesson_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "lesson_not_found", "message": "Esta lição não existe."},
        )
    return detail


@router.get(
    "/signs",
    response_model=list[SignView],
    summary="Search signs by Portuguese term (dictionary)",
)
async def search_signs(
    q: str = Query(default="", min_length=0, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    repo: SignRepository = Depends(get_sign_repo),
) -> list[SignView]:
    signs = await repo.search_by_term(q, limit=limit) if q else await repo.list(limit=limit)
    return [SignView.from_sign(s) for s in signs]
