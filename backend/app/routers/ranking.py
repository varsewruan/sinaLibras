"""/ranking — global leaderboard by XP."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.deps import get_ranking_service, optional_current_user
from app.models.ranking import RankingResponse
from app.models.user import User
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get(
    "",
    response_model=RankingResponse,
    summary="Top players by XP, plus the caller's own position",
)
async def leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    user: Optional[User] = Depends(optional_current_user),
    service: RankingService = Depends(get_ranking_service),
) -> RankingResponse:
    return await service.leaderboard(me=user, limit=limit)
