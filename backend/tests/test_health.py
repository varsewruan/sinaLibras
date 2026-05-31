"""Health endpoints."""


async def test_healthz_returns_alive(client):
    r = await client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


async def test_readyz_pings_db(client):
    r = await client.get("/api/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


async def test_root_returns_metadata(client):
    r = await client.get("/api/")
    body = r.json()
    assert r.status_code == 200
    assert "name" in body and "version" in body
