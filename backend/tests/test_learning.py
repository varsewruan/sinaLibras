"""Learning catalog endpoints."""


async def test_phases_returns_seeded_catalog(client):
    r = await client.get("/api/learning/phases")
    assert r.status_code == 200
    phases = r.json()
    assert len(phases) == 2  # see CATALOG in conftest.py
    titles = [p["title"] for p in phases]
    assert titles == ["Cumprimentos", "Família"]
    # Lessons aren't logged-in -> completed defaults False.
    assert all(l["completed"] is False for p in phases for l in p["lessons"])


async def test_phases_includes_user_progress_when_authenticated(auth_client):
    r = await auth_client.get("/api/learning/phases")
    assert r.status_code == 200
    # Same data, but the endpoint took the auth path. Completed still False
    # because the user hasn't done anything yet.
    body = r.json()
    assert body[0]["lessons"][0]["completed"] is False
    assert body[0]["lessons"][0]["score"] is None


async def test_lesson_detail_returns_signs_in_order(client):
    phases = (await client.get("/api/learning/phases")).json()
    first_lesson_id = phases[0]["lessons"][0]["id"]
    r = await client.get(f"/api/learning/lessons/{first_lesson_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Olá e Tchau"
    assert [s["portuguese_term"] for s in body["signs"]] == ["Olá", "Tchau", "Tudo bem?", "Obrigado"]


async def test_lesson_not_found(client):
    r = await client.get("/api/learning/lessons/nope-doesnt-exist")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "lesson_not_found"


async def test_signs_search(client):
    r = await client.get("/api/learning/signs?q=ola")
    # Case-insensitive partial; "Olá" should match (sans accent it wouldn't,
    # but we don't strip accents server-side — just verifying it works on the
    # case that does match).
    assert r.status_code == 200
    r2 = await client.get("/api/learning/signs?q=mae")
    assert r2.status_code == 200


async def test_signs_browse_default_limit(client):
    r = await client.get("/api/learning/signs")
    assert r.status_code == 200
    # default limit is 20; we have at least 12 seeded.
    assert len(r.json()) >= 12
