"""Authentication flows: register, login, me, refresh, logout, edge cases."""

import pytest


CREDS = {"email": "alice@example.com", "name": "Alice", "password": "supersecret"}


async def test_register_sets_cookies_and_returns_user(client):
    r = await client.post("/api/auth/register", json=CREDS)
    assert r.status_code == 201
    assert r.json()["user"]["email"] == CREDS["email"]
    assert r.json()["user"]["xp"] == 0
    assert "access_token" in client.cookies
    assert "refresh_token" in client.cookies


async def test_me_returns_user_with_cookies(client):
    await client.post("/api/auth/register", json=CREDS)
    r = await client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == CREDS["email"]


async def test_me_without_cookies_returns_401(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "missing_access_token"


async def test_duplicate_register_returns_409(client):
    await client.post("/api/auth/register", json=CREDS)
    r = await client.post("/api/auth/register", json={**CREDS, "name": "Other"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "email_taken"


async def test_login_with_correct_password(client):
    await client.post("/api/auth/register", json=CREDS)
    # Clear cookies to simulate a fresh session.
    client.cookies.clear()
    r = await client.post("/api/auth/login", json={"email": CREDS["email"], "password": CREDS["password"]})
    assert r.status_code == 200
    assert "access_token" in client.cookies


async def test_login_wrong_password_returns_401(client):
    await client.post("/api/auth/register", json=CREDS)
    client.cookies.clear()
    r = await client.post("/api/auth/login", json={"email": CREDS["email"], "password": "WRONG"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "invalid_credentials"


async def test_login_unknown_email_returns_401(client):
    r = await client.post("/api/auth/login", json={"email": "ghost@x.com", "password": "anything"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "invalid_credentials"


async def test_refresh_issues_new_tokens(client):
    await client.post("/api/auth/register", json=CREDS)
    original_access = client.cookies.get("access_token")
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 200
    assert client.cookies.get("access_token") != original_access


async def test_logout_revokes_subsequent_tokens(client):
    await client.post("/api/auth/register", json=CREDS)
    r = await client.post("/api/auth/logout")
    assert r.status_code == 204

    # Even if the SPA had cached the old access token, hitting /me with it
    # must fail because token_version was bumped.
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.parametrize("payload, field", [
    ({"email": "not-an-email", "name": "x", "password": "supersecret"}, "email"),
    ({"email": "ok@x.com",     "name": "",  "password": "supersecret"}, "name"),
    ({"email": "ok@x.com",     "name": "x", "password": "short"},        "password"),
    ({"email": "ok@x.com",     "name": "x", "password": "password"},     "password"),  # common
])
async def test_register_validation(client, payload, field):
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 422
    locs = [".".join(map(str, err["loc"])) for err in r.json()["detail"]]
    assert any(field in loc for loc in locs), f"expected {field} error, got {locs}"


async def test_email_normalization(client):
    await client.post("/api/auth/register", json={**CREDS, "email": "ALICE@example.COM"})
    client.cookies.clear()
    r = await client.post("/api/auth/login", json={"email": CREDS["email"], "password": CREDS["password"]})
    assert r.status_code == 200, "lookup should match regardless of case"
