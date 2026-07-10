"""Achievements ("conquistas").

Achievements are *derived*, never stored: an achievement is unlocked exactly
when the user's current stats clear its target. That keeps them consistent
with XP/streak/lesson counts by construction — there is no unlock record that
can drift out of sync, and re-tuning a target instantly re-evaluates everyone.

The trade-off: we can't show "unlocked on <date>". Add a per-user unlock
collection if that becomes a requirement.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from pydantic import BaseModel


class Metric(str, Enum):
    """Which user stat an achievement is measured against."""

    XP = "xp"
    STREAK = "streak"      # longest streak ever reached, not the current one
    LESSONS = "lessons"    # lessons completed


class AchievementDef(NamedTuple):
    id: str
    title: str
    description: str
    icon: str      # lucide icon name; the SPA maps it to a component
    metric: Metric
    target: int


# Ordered by metric, then by target — the UI renders them in this order.
CATALOG: tuple[AchievementDef, ...] = (
    AchievementDef("xp-100",   "Primeiros passos", "Alcance 100 de XP.",   "Sparkles", Metric.XP, 100),
    AchievementDef("xp-500",   "Aprendiz dedicado", "Alcance 500 de XP.",  "Star",     Metric.XP, 500),
    AchievementDef("xp-1000",  "Mestre do XP",     "Alcance 1000 de XP.",  "Trophy",   Metric.XP, 1000),
    AchievementDef("xp-2500",  "Lenda de Libras",  "Alcance 2500 de XP.",  "Crown",    Metric.XP, 2500),

    AchievementDef("streak-3",  "Fogo aceso",       "Acenda o fogo por 3 dias consecutivos.",  "Flame",     Metric.STREAK, 3),
    AchievementDef("streak-7",  "Semana em chamas", "Acenda o fogo por 7 dias consecutivos.",  "Flame",     Metric.STREAK, 7),
    AchievementDef("streak-10", "Incendiário",      "Acenda o fogo por 10 dias consecutivos.", "Flame",     Metric.STREAK, 10),
    AchievementDef("streak-30", "Chama eterna",     "Acenda o fogo por 30 dias consecutivos.", "Flame",     Metric.STREAK, 30),

    AchievementDef("lessons-1",  "Primeira lição",     "Conclua sua primeira lição.", "BookCheck", Metric.LESSONS, 1),
    AchievementDef("lessons-5",  "Ritmo constante",    "Conclua 5 lições.",           "BookCheck", Metric.LESSONS, 5),
    AchievementDef("lessons-10", "Estudante aplicado", "Conclua 10 lições.",          "GraduationCap", Metric.LESSONS, 10),
    AchievementDef("lessons-25", "Fluência à vista",   "Conclua 25 lições.",          "GraduationCap", Metric.LESSONS, 25),
)


class AchievementView(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    metric: Metric
    target: int
    progress: int   # capped at target, so the UI can render progress/target directly
    unlocked: bool


class AchievementsResponse(BaseModel):
    achievements: list[AchievementView]
    unlocked_count: int
    total: int
