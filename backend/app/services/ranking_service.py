"""Leaderboard rules: who is ahead of whom, and where do *I* sit."""

from __future__ import annotations

from typing import Optional

from app.models.ranking import RankingEntry, RankingResponse
from app.models.user import User
from app.repositories.user_repo import UserRepository


class RankingService:
    def __init__(self, *, users: UserRepository) -> None:
        self.users = users

    async def leaderboard(
        self, *, me: Optional[User] = None, limit: int = 20
    ) -> RankingResponse:
        top = await self.users.top_by_xp(limit=limit)

        entries = [
            RankingEntry.from_user(u, rank=rank, is_me=bool(me and u.id == me.id))
            for u, rank in zip(top, _competition_ranks(top))
        ]

        if me is None:
            return RankingResponse(entries=entries, me=None)

        # Already on the visible page → reuse that row (it has the true rank).
        mine = next((e for e in entries if e.is_me), None)
        if mine is None:
            # Outside the top-N: derive the rank without paging the collection.
            # Agrees with _competition_ranks by construction — both answer
            # "how many users are strictly ahead of me, plus one".
            rank = await self.users.count_with_more_xp(me.xp) + 1
            mine = RankingEntry.from_user(me, rank=rank, is_me=True)

        return RankingResponse(entries=entries, me=mine)


def _competition_ranks(users: list[User]) -> list[int]:
    """Standard competition ranking ("1224") over an XP-descending page.

    Users tied on XP share a rank, and the next distinct XP resumes at the
    positional index. Naive enumerate() would hand tied users different ranks,
    which then disagrees with the count-based rank we compute for a caller
    who falls outside the page — the same user would see a different number
    depending on `limit`.

    Correct only because the page always starts at the overall #1 (no offset).
    """
    ranks: list[int] = []
    prev_xp: Optional[int] = None
    prev_rank = 0

    for position, user in enumerate(users, start=1):
        if user.xp == prev_xp:
            ranks.append(prev_rank)
        else:
            ranks.append(position)
            prev_xp = user.xp
            prev_rank = position

    return ranks
