"""
Progress + gamification rules.

Single place that owns:
  - what counts as "passed" (>= 60% by default);
  - how XP is awarded (proportional to score, capped at lesson.xp_reward);
  - how the streak advances (today/yesterday/older);
  - the upsert into the `progress` collection.

Routes are thin wrappers that translate HTTP to/from this layer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.base import utc_now
from app.models.progress import CompleteLessonRequest, CompleteLessonResponse, Progress
from app.models.user import StreakState, User, UserPublic
from app.repositories.lesson_repo import LessonRepository
from app.repositories.progress_repo import ProgressRepository
from app.repositories.user_repo import UserRepository


PASS_THRESHOLD = 60  # percent


class ProgressError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ProgressService:
    def __init__(
        self,
        *,
        users: UserRepository,
        lessons: LessonRepository,
        progress: ProgressRepository,
    ) -> None:
        self.users = users
        self.lessons = lessons
        self.progress = progress

    async def complete_lesson(
        self, *, user: User, payload: CompleteLessonRequest
    ) -> CompleteLessonResponse:
        lesson = await self.lessons.get(payload.lesson_id)
        if lesson is None:
            raise ProgressError("lesson_not_found", "Esta lição não existe.")

        passed = payload.score >= PASS_THRESHOLD
        existing = await self.progress.get_for_user_lesson(user.id, lesson.id)

        # Only award XP the FIRST time the user passes. Replays improve the
        # recorded score but don't farm XP — keeps the economy honest.
        already_passed = bool(existing and existing.completed)
        awarded_xp = 0
        if passed and not already_passed:
            awarded_xp = round(lesson.xp_reward * payload.score / 100)

        # Upsert progress.
        if existing is None:
            progress = Progress(
                user_id=user.id,
                lesson_id=lesson.id,
                score=payload.score,
                completed=passed,
                completed_at=utc_now() if passed else None,
                attempts=1,
            )
            await self.progress.insert(progress)
        else:
            # Keep the best score; mark completed the first time it passes.
            new_score = max(existing.score, payload.score)
            completed = existing.completed or passed
            completed_at = existing.completed_at or (utc_now() if passed else None)
            existing.score = new_score
            existing.completed = completed
            existing.completed_at = completed_at
            existing.attempts = existing.attempts + 1
            existing.touch()
            await self.progress.replace(existing)
            progress = existing

        # Update user XP + streak.
        new_streak = _advance_streak(user.streak, today=utc_now())
        new_xp = user.xp + awarded_xp
        updated = await self.users.update_fields(
            user.id,
            {
                "xp": new_xp,
                "streak": new_streak.model_dump(),
                "updated_at": utc_now(),
            },
        )
        # update_fields returns the post-update document; fall back to a
        # locally-rebuilt one if Mongo returned nothing (shouldn't happen).
        final_user = updated or user.model_copy(update={"xp": new_xp, "streak": new_streak})

        return CompleteLessonResponse(
            progress=progress,
            user=UserPublic.from_user(final_user),
            awarded_xp=awarded_xp,
            passed=passed,
            streak=new_streak,
        )

    async def summary_for(self, user: User) -> dict:
        """Lightweight aggregate for the Profile screen."""
        all_progress = await self.progress.list_for_user(user.id, limit=1000)
        completed = [p for p in all_progress if p.completed]
        return {
            "lessons_started": len(all_progress),
            "lessons_completed": len(completed),
            "best_average": (
                round(sum(p.score for p in completed) / len(completed)) if completed else 0
            ),
        }


# -------------------- Streak math --------------------------------------------

def _advance_streak(current: StreakState, *, today: datetime) -> StreakState:
    """Pure function: streak rules only depend on the day delta.

    Rules:
      - Never active before  → current = 1, longest = max(1, prev.longest)
      - Active today already → unchanged
      - Active yesterday     → current += 1
      - Active >1 day ago    → reset to 1
    """
    last = current.last_activity_at
    today_d = today.date()

    if last is None:
        new_current = 1
    else:
        # Normalize to UTC day for comparison; tolerate naive timestamps.
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        last_d = last.date()
        delta = (today_d - last_d).days
        if delta == 0:
            new_current = max(current.current, 1)
        elif delta == 1:
            new_current = current.current + 1
        else:
            new_current = 1

    return StreakState(
        current=new_current,
        longest=max(current.longest, new_current),
        last_activity_at=today,
    )
