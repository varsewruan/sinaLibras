"""Progress endpoints — completion + per-user summary."""

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.deps import get_current_user, get_progress_service
from app.models.progress import CompleteLessonRequest, CompleteLessonResponse
from app.models.user import User
from app.services.progress_service import ProgressError, ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post(
    "/complete-lesson",
    response_model=CompleteLessonResponse,
    summary="Record a lesson attempt; award XP if passed",
)
async def complete_lesson(
    payload: CompleteLessonRequest = Body(...),
    user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
) -> CompleteLessonResponse:
    try:
        return await service.complete_lesson(user=user, payload=payload)
    except ProgressError as exc:
        code_to_status = {
            "lesson_not_found": status.HTTP_404_NOT_FOUND,
        }
        raise HTTPException(
            status_code=code_to_status.get(exc.code, status.HTTP_400_BAD_REQUEST),
            detail={"code": exc.code, "message": exc.message},
        )


@router.get("/me/summary", summary="Per-user progress summary for the Profile page")
async def my_summary(
    user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
) -> dict:
    return await service.summary_for(user)
