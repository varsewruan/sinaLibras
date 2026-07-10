"""Evaluate the achievement catalog against a user's current stats."""

from __future__ import annotations

from app.models.achievement import (
    CATALOG,
    AchievementDef,
    AchievementsResponse,
    AchievementView,
    Metric,
)
from app.models.user import User
from app.repositories.progress_repo import ProgressRepository


class AchievementService:
    def __init__(self, *, progress: ProgressRepository) -> None:
        self.progress = progress

    async def for_user(self, user: User) -> AchievementsResponse:
        stats = {
            Metric.XP: user.xp,
            # Longest, not current: an achievement already earned shouldn't
            # disappear the day the user breaks their streak.
            Metric.STREAK: user.streak.longest,
            Metric.LESSONS: await self.progress.count_completed(user.id),
        }

        views = [_evaluate(d, stats[d.metric]) for d in CATALOG]
        return AchievementsResponse(
            achievements=views,
            unlocked_count=sum(v.unlocked for v in views),
            total=len(views),
        )


def _evaluate(definition: AchievementDef, value: int) -> AchievementView:
    return AchievementView(
        id=definition.id,
        title=definition.title,
        description=definition.description,
        icon=definition.icon,
        metric=definition.metric,
        target=definition.target,
        progress=min(value, definition.target),
        unlocked=value >= definition.target,
    )
