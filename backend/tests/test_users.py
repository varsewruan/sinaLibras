"""PATCH /users/me — avatar selection."""

import pytest


@pytest.mark.asyncio
async def test_new_user_gets_the_dummy_avatar(auth_client):
    r = await auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["avatar"] == "dummy"


@pytest.mark.asyncio
async def test_update_avatar_persists(auth_client):
    # "dummy" custa 0, então está disponível sem compra. Avatares pagos são
    # recusados aqui de propósito — ver test_paid_avatar_requires_purchase.
    r = await auth_client.patch("/api/users/me", json={"avatar": "dummy"})
    assert r.status_code == 200, r.text
    assert r.json()["avatar"] == "dummy"

    # Survives a fresh read, i.e. it actually hit Mongo.
    again = await auth_client.get("/api/auth/me")
    assert again.json()["avatar"] == "dummy"


@pytest.mark.asyncio
async def test_paid_avatar_requires_purchase(auth_client):
    """PATCH /users/me não pode ser um atalho grátis em volta da loja."""
    r = await auth_client.patch("/api/users/me", json={"avatar": "unicorn"})
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "not_owned"

    # ...e o avatar continua o mesmo.
    me = await auth_client.get("/api/auth/me")
    assert me.json()["avatar"] == "dummy"


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
