"""
Read-side composition for the learning content.

The Path screen needs phases + their lessons + a `completed` flag per
lesson for the current user. Doing that in three repositories at the
route layer would be ugly; this service is the single place that knows
how to stitch the view together.
"""

from __future__ import annotations

from typing import Optional

from app.models.learning import LessonDetail, LessonSummary, PhaseWithLessons, SignView
from app.repositories.lesson_repo import LessonRepository
from app.repositories.phase_repo import PhaseRepository
from app.repositories.progress_repo import ProgressRepository
from app.repositories.sign_repo import SignRepository


class LearningService:
    def __init__(
        self,
        *,
        phases: PhaseRepository,
        lessons: LessonRepository,
        signs: SignRepository,
        progress: ProgressRepository,
    ) -> None:
        self.phases = phases
        self.lessons = lessons
        self.signs = signs
        self.progress = progress

    async def list_phases_with_lessons(
        self, *, user_id: Optional[str] = None
    ) -> list[PhaseWithLessons]:
        phases = await self.phases.list_ordered()
        if not phases:
            return []

        # One Mongo round-trip per phase is fine at this scale; tune to a
        # single aggregate pipeline when the catalog grows past ~100 lessons.
        result: list[PhaseWithLessons] = []
        for phase in phases:
            lessons = await self.lessons.list_by_phase(phase.id)
            progress_index = {}
            if user_id and lessons:
                # Index user progress for this phase's lessons by lesson_id.
                lesson_ids = [lesson.id for lesson in lessons]
                user_progress = await self.progress.list(
                    filter={"user_id": user_id, "lesson_id": {"$in": lesson_ids}},
                    limit=len(lesson_ids),
                )
                progress_index = {p.lesson_id: p for p in user_progress}

            summaries = [
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    description=lesson.description,
                    order=lesson.order,
                    xp_reward=lesson.xp_reward,
                    sign_count=len(lesson.sign_ids),
                    completed=bool(progress_index.get(lesson.id, None) and progress_index[lesson.id].completed),
                    score=progress_index[lesson.id].score if lesson.id in progress_index else None,
                )
                for lesson in lessons
            ]
            result.append(
                PhaseWithLessons(
                    id=phase.id,
                    title=phase.title,
                    description=phase.description,
                    order=phase.order,
                    lessons=summaries,
                )
            )
        return result

    async def get_lesson_detail(self, lesson_id: str) -> Optional[LessonDetail]:
        lesson = await self.lessons.get(lesson_id)
        if lesson is None:
            return None
        signs_full = []
        if lesson.sign_ids:
            # Preserve the order declared in the lesson, not the order the DB
            # happens to return them in.
            fetched = await self.signs.list(
                filter={"_id": {"$in": lesson.sign_ids}},
                limit=len(lesson.sign_ids),
            )
            by_id = {sign.id: sign for sign in fetched}
            signs_full = [by_id[sid] for sid in lesson.sign_ids if sid in by_id]

        return LessonDetail(
            id=lesson.id,
            phase_id=lesson.phase_id,
            title=lesson.title,
            description=lesson.description,
            order=lesson.order,
            xp_reward=lesson.xp_reward,
            signs=[SignView.from_sign(sign) for sign in signs_full],
        )
