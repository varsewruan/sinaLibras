"""/achievements — the caller's conquistas, derived from their stats."""

from fastapi import APIRouter, Depends

from app.deps import get_achievement_service, get_current_user
from app.models.achievement import AchievementsResponse
from app.models.user import User
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get(
    "/me",
    response_model=AchievementsResponse,
    summary="Achievement catalog evaluated against the current user",
)
async def my_achievements(
    user: User = Depends(get_current_user),
    service: AchievementService = Depends(get_achievement_service),
) -> AchievementsResponse:
    return await service.for_user(user)
