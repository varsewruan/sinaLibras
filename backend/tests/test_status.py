"""Status CRUD — the canary endpoint kept from the template."""


async def test_create_and_list_status(client):
    r = await client.post("/api/status", json={"client_name": "ci"})
    assert r.status_code == 201
    body = r.json()
    assert body["client_name"] == "ci"
    assert "id" in body and "_id" not in body  # contract: API uses `id`
    created_id = body["id"]

    r = await client.get("/api/status?limit=10")
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert created_id in ids


async def test_create_status_rejects_empty_name(client):
    r = await client.post("/api/status", json={"client_name": ""})
    assert r.status_code == 422


async def test_list_status_pagination_bounds(client):
    r = await client.get("/api/status?limit=0")
    assert r.status_code == 422  # ge=1
    r = await client.get("/api/status?limit=999")
    assert r.status_code == 422  # le=200
