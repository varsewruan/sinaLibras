"""PATCH /users/me — avatar selection."""

import pytest


@pytest.mark.asyncio
async def test_new_user_gets_the_dummy_avatar(auth_client):
    r = await auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["avatar"] == "dummy"


@pytest.mark.asyncio
async def test_update_avatar_persists(auth_client):
    r = await auth_client.patch("/api/users/me", json={"avatar": "fox"})
    assert r.status_code == 200, r.text
    assert r.json()["avatar"] == "fox"

    # Survives a fresh read, i.e. it actually hit Mongo.
    again = await auth_client.get("/api/auth/me")
    assert again.json()["avatar"] == "fox"


@pytest.mark.asyncio
async def test_unknown_preset_is_rejected(auth_client):
    r = await auth_client.patch("/api/users/me", json={"avatar": "not-a-preset"})
    assert r.status_code == 422

    # ...and the stored avatar is untouched.
    me = await auth_client.get("/api/auth/me")
    assert me.json()["avatar"] == "dummy"


@pytest.mark.asyncio
async def test_avatar_requires_auth(client):
    r = await client.patch("/api/users/me", json={"avatar": "fox"})
    assert r.status_code == 401
