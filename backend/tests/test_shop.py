"""Loja — compra com XP, posse e equipamento."""

import pytest

from app.db.mongo import get_db


async def _grant_xp(email: str, xp: int) -> None:
    """Dá XP direto no banco.

    Ganhar XP pela API exigiria completar lições de verdade, o que testaria o
    progresso, não a loja.
    """
    await get_db()["users"].update_one({"email": email}, {"$set": {"xp": xp}})


EMAIL = "tester@example.com"  # o usuário criado pela fixture auth_client


@pytest.mark.asyncio
async def test_catalog_marks_free_items_as_owned(auth_client):
    r = await auth_client.get("/api/shop/items")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["balance"] == 0
    by_id = {item["id"]: item for item in body["items"]}
    # Preço 0 conta como possuído sem nunca ter sido comprado — senão uma
    # conta nova ficaria sem nenhum avatar utilizável.
    assert by_id["dummy"]["owned"] is True
    assert by_id["dummy"]["equipped"] is True
    assert by_id["unicorn"]["owned"] is False


@pytest.mark.asyncio
async def test_purchase_spends_balance_without_touching_xp(auth_client):
    """O ponto central: comprar não pode derrubar ranking nem nível."""
    await _grant_xp(EMAIL, 500)

    r = await auth_client.post("/api/shop/purchase", json={"item_id": "acc-oculos-vermelho"})
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["xp"] == 500          # total intacto → ranking/nível intactos
    assert body["xp_spent"] == 50
    assert body["xp_balance"] == 450


@pytest.mark.asyncio
async def test_purchase_rejected_without_enough_balance(auth_client):
    await _grant_xp(EMAIL, 30)

    r = await auth_client.post("/api/shop/purchase", json={"item_id": "acc-oculos-vermelho"})
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "insufficient_xp"

    me = await auth_client.get("/api/auth/me")
    assert me.json()["xp_spent"] == 0


@pytest.mark.asyncio
async def test_buying_twice_does_not_charge_twice(auth_client):
    """Duplo clique não pode cobrar duas vezes."""
    await _grant_xp(EMAIL, 500)

    first = await auth_client.post("/api/shop/purchase", json={"item_id": "acc-bone"})
    assert first.status_code == 200
    assert first.json()["xp_spent"] == 80

    second = await auth_client.post("/api/shop/purchase", json={"item_id": "acc-bone"})
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "already_owned"

    me = await auth_client.get("/api/auth/me")
    assert me.json()["xp_spent"] == 80


@pytest.mark.asyncio
async def test_price_comes_from_the_catalog_not_the_request(auth_client):
    """O cliente manda só o id; mandar um preço junto não muda a cobrança."""
    await _grant_xp(EMAIL, 2000)

    r = await auth_client.post(
        "/api/shop/purchase",
        json={"item_id": "acc-coroa", "price": 1},
    )
    assert r.status_code == 200, r.text
    assert r.json()["xp_spent"] == 1000  # preço do catálogo, não o do request


@pytest.mark.asyncio
async def test_equip_requires_ownership(auth_client):
    r = await auth_client.post("/api/shop/equip", json={"item_id": "acc-coroa"})
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "not_owned"


@pytest.mark.asyncio
async def test_purchase_then_equip_avatar_and_accessory(auth_client):
    await _grant_xp(EMAIL, 2000)

    await auth_client.post("/api/shop/purchase", json={"item_id": "unicorn"})
    await auth_client.post("/api/shop/purchase", json={"item_id": "acc-coroa"})

    avatar = await auth_client.post("/api/shop/equip", json={"item_id": "unicorn"})
    assert avatar.status_code == 200, avatar.text
    assert avatar.json()["avatar"] == "unicorn"

    # Acessório é campo separado: bicho e chapéu coexistem.
    acc = await auth_client.post("/api/shop/equip", json={"item_id": "acc-coroa"})
    assert acc.status_code == 200, acc.text
    assert acc.json()["accessory"] == "acc-coroa"
    assert acc.json()["avatar"] == "unicorn"

    off = await auth_client.post("/api/shop/unequip")
    assert off.status_code == 200
    assert off.json()["accessory"] is None


@pytest.mark.asyncio
async def test_unknown_item_is_404(auth_client):
    r = await auth_client.post("/api/shop/purchase", json={"item_id": "nao-existe"})
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "item_not_found"


@pytest.mark.asyncio
async def test_shop_requires_auth(client):
    assert (await client.get("/api/shop/items")).status_code == 401
