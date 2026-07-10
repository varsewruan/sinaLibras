"""GET /achievements/me — the catalog evaluated against real user stats."""

import pytest

from app.db.mongo import get_db


def _by_id(body: dict) -> dict:
    return {a["id"]: a for a in body["achievements"]}


@pytest.mark.asyncio
async def test_fresh_user_has_nothing_unlocked(auth_client):
    r = await auth_client.get("/api/achievements/me")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["unlocked_count"] == 0
    assert body["total"] == len(body["achievements"])
    assert all(a["unlocked"] is False for a in body["achievements"])
    assert all(a["progress"] == 0 for a in body["achievements"])


@pytest.mark.asyncio
async def test_completing_a_lesson_unlocks_the_first_achievements(auth_client):
    phases = (await auth_client.get("/api/learning/phases")).json()
    lesson = phases[0]["lessons"][0]

    await auth_client.post(
        "/api/progress/complete-lesson",
        json={"lesson_id": lesson["id"], "score": 100},
    )

    body = (await auth_client.get("/api/achievements/me")).json()
    ach = _by_id(body)

    assert ach["lessons-1"]["unlocked"] is True
    assert ach["lessons-1"]["progress"] == 1
    # First lesson also starts the streak.
    assert ach["streak-3"]["progress"] == 1
    assert ach["streak-3"]["unlocked"] is False
    assert body["unlocked_count"] >= 1


@pytest.mark.asyncio
async def test_progress_is_capped_at_the_target(auth_client):
    """A user far past a target reports progress == target, not the raw stat."""
    me = (await auth_client.get("/api/auth/me")).json()
    db = get_db()
    await db.users.update_one({"_id": me["id"]}, {"$set": {"xp": 9999}})

    ach = _by_id((await auth_client.get("/api/achievements/me")).json())

    assert ach["xp-100"]["unlocked"] is True
    assert ach["xp-100"]["progress"] == 100  # capped, not 9999
    assert ach["xp-2500"]["unlocked"] is True
    assert ach["xp-2500"]["progress"] == 2500


@pytest.mark.asyncio
async def test_streak_achievements_use_the_longest_streak(auth_client):
    """An earned streak badge must not vanish when the current streak breaks."""
    me = (await auth_client.get("/api/auth/me")).json()
    db = get_db()
    await db.users.update_one(
        {"_id": me["id"]},
        {"$set": {"streak.current": 0, "streak.longest": 12}},
    )

    ach = _by_id((await auth_client.get("/api/achievements/me")).json())

    assert ach["streak-10"]["unlocked"] is True
    assert ach["streak-30"]["progress"] == 12


@pytest.mark.asyncio
async def test_achievements_require_auth(client):
    r = await client.get("/api/achievements/me")
    assert r.status_code == 401
