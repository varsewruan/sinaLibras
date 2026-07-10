"""GET /ranking — leaderboard ordering and self-placement."""

import pytest

from app.db.mongo import get_db
from app.models.user import StreakState, User


async def _insert_user(name: str, xp: int) -> str:
    db = get_db()
    user = User(
        email=f"{name.lower()}@example.com",
        name=name,
        hashed_password="x" * 20,
        xp=xp,
        streak=StreakState(current=xp // 100, longest=xp // 100),
    )
    await db.users.insert_one(user.to_mongo())
    return user.id


@pytest.mark.asyncio
async def test_ranking_is_sorted_by_xp_desc(auth_client):
    await _insert_user("Alta", 500)
    await _insert_user("Media", 300)
    await _insert_user("Baixa", 100)

    r = await auth_client.get("/api/ranking")
    assert r.status_code == 200, r.text
    entries = r.json()["entries"]

    xps = [e["xp"] for e in entries]
    assert xps == sorted(xps, reverse=True)
    assert [e["rank"] for e in entries] == list(range(1, len(entries) + 1))
    assert entries[0]["name"] == "Alta"


@pytest.mark.asyncio
async def test_ranking_marks_and_places_the_caller(auth_client):
    # The registered tester has 0 XP, so three richer users push them to rank 4.
    for name, xp in [("Alta", 500), ("Media", 300), ("Baixa", 100)]:
        await _insert_user(name, xp)

    r = await auth_client.get("/api/ranking")
    body = r.json()

    me = body["me"]
    assert me is not None
    assert me["is_me"] is True
    assert me["rank"] == 4
    # On the page (limit=20 > 4 users), so the inline row is flagged too.
    assert any(e["is_me"] for e in body["entries"])


@pytest.mark.asyncio
async def test_caller_outside_the_page_is_still_placed(auth_client):
    for i in range(5):
        await _insert_user(f"Rico{i}", 1000 + i)

    r = await auth_client.get("/api/ranking?limit=2")
    body = r.json()

    assert len(body["entries"]) == 2
    assert not any(e["is_me"] for e in body["entries"])
    # Pinned separately, with the true rank behind the 5 richer players.
    assert body["me"]["rank"] == 6
    assert body["me"]["is_me"] is True


@pytest.mark.asyncio
async def test_tied_users_share_a_rank(auth_client):
    """Competition ranking: 500, 300, 300, 100 → ranks 1, 2, 2, 4."""
    await _insert_user("Alta", 500)
    await _insert_user("EmpateA", 300)
    await _insert_user("EmpateB", 300)
    await _insert_user("Baixa", 100)

    r = await auth_client.get("/api/ranking")
    by_name = {e["name"]: e["rank"] for e in r.json()["entries"]}

    assert by_name["Alta"] == 1
    assert by_name["EmpateA"] == 2
    assert by_name["EmpateB"] == 2
    assert by_name["Baixa"] == 4  # not 3 — the tie consumed a slot


@pytest.mark.asyncio
async def test_own_rank_does_not_depend_on_limit(auth_client):
    """The caller's rank must be the same whether or not they fit on the page.

    Regression: positional ranks gave a tied user a different number when they
    appeared inline vs. when they were pinned from outside the page.
    """
    for i in range(3):
        await _insert_user(f"Rico{i}", 900 + i)
    # Two more users tied with the caller on 0 XP.
    await _insert_user("Zero1", 0)
    await _insert_user("Zero2", 0)

    on_page = await auth_client.get("/api/ranking?limit=20")
    off_page = await auth_client.get("/api/ranking?limit=2")

    assert any(e["is_me"] for e in on_page.json()["entries"])
    assert not any(e["is_me"] for e in off_page.json()["entries"])
    # 3 users ahead → rank 4 for everyone tied at 0 XP, either way.
    assert on_page.json()["me"]["rank"] == 4
    assert off_page.json()["me"]["rank"] == 4


@pytest.mark.asyncio
async def test_ranking_never_leaks_emails(auth_client):
    await _insert_user("Alta", 500)
    r = await auth_client.get("/api/ranking")
    for entry in r.json()["entries"]:
        assert "email" not in entry


@pytest.mark.asyncio
async def test_ranking_is_readable_anonymously(client):
    await _insert_user("Alta", 500)
    r = await client.get("/api/ranking")
    assert r.status_code == 200
    assert r.json()["me"] is None
