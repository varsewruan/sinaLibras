"""
As mensagens de erro que o usuário lê saem em português — e o `code`, que é
contrato de máquina, continua em inglês.

O teste procura por caracteres/palavras que só existem no texto traduzido em
vez de comparar a frase inteira, pra não quebrar a cada ajuste de redação.
"""

import pytest

EMAIL = "erros@sinalibras.dev"
SENHA = "senha-boa-123"


async def _registrar(client) -> None:
    r = await client.post(
        "/api/auth/register",
        json={"email": EMAIL, "name": "Erro Tester", "password": SENHA},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_credencial_invalida_responde_em_portugues(client):
    await _registrar(client)
    r = await client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": "senha-totalmente-errada"},
    )
    assert r.status_code == 401
    detail = r.json()["detail"]
    # O code é o contrato — segue em inglês.
    assert detail["code"] == "invalid_credentials"
    assert "incorretos" in detail["message"]


@pytest.mark.asyncio
async def test_email_duplicado_responde_em_portugues(client):
    await _registrar(client)
    r = await client.post(
        "/api/auth/register",
        json={"email": EMAIL, "name": "Outro", "password": SENHA},
    )
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "email_taken"
    assert "já está cadastrado" in detail["message"]


@pytest.mark.asyncio
async def test_licao_inexistente_responde_em_portugues(client):
    r = await client.get("/api/learning/lessons/nao-existe")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["code"] == "lesson_not_found"
    assert "não existe" in detail["message"]


@pytest.mark.asyncio
async def test_sem_cookie_responde_em_portugues(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    detail = r.json()["detail"]
    assert detail["code"] == "missing_access_token"
    assert "Entre na sua conta" in detail["message"]


# ---------------- 422 do pydantic -------------------------------------------


@pytest.mark.asyncio
async def test_campo_faltando_nomeia_o_campo_em_portugues(client):
    r = await client.post("/api/auth/register", json={})
    assert r.status_code == 422
    msgs = [e["msg"] for e in r.json()["detail"]]
    assert "Informe o e-mail." in msgs
    assert "Informe o nome." in msgs
    assert "Informe a senha." in msgs


@pytest.mark.asyncio
async def test_senha_curta_responde_em_portugues(client):
    r = await client.post(
        "/api/auth/register",
        json={"email": "curta@sinalibras.dev", "name": "X", "password": "abc"},
    )
    assert r.status_code == 422
    msgs = [e["msg"] for e in r.json()["detail"]]
    assert "A senha deve ter pelo menos 8 caracteres." in msgs


@pytest.mark.asyncio
async def test_email_invalido_responde_em_portugues(client):
    r = await client.post(
        "/api/auth/register",
        json={"email": "nao-e-email", "name": "X", "password": "senha-boa-123"},
    )
    assert r.status_code == 422
    assert "E-mail inválido." in [e["msg"] for e in r.json()["detail"]]


@pytest.mark.asyncio
async def test_senha_comum_perde_o_prefixo_do_pydantic(client):
    """`raise ValueError` vira "Value error, ..." — o prefixo tem que sumir."""
    r = await client.post(
        "/api/auth/register",
        json={"email": "comum@sinalibras.dev", "name": "X", "password": "password"},
    )
    assert r.status_code == 422
    msgs = [e["msg"] for e in r.json()["detail"]]
    assert "Esta senha é muito comum. Escolha outra." in msgs
    assert not any(m.startswith("Value error") for m in msgs)


@pytest.mark.asyncio
async def test_422_mantem_o_formato_que_o_spa_espera(client):
    """
    O front faz `Array.isArray(detail) ? detail[0].msg : detail.message`.
    Traduzir é mudança de apresentação, não de contrato.
    """
    r = await client.post("/api/auth/register", json={})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert isinstance(detail, list)
    assert all("msg" in e and "loc" in e and "type" in e for e in detail)


# ---------------- 429 do slowapi --------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_responde_no_formato_do_contrato(client, apertar_rate_limit):
    """
    O handler embutido do slowapi responde `{"error": "Rate limit exceeded:
    ..."}` — sem `detail`, e em inglês. O SPA lia `detail.message`, não achava
    nada e caía no genérico "Falha ao criar conta.", escondendo justamente a
    única informação útil: que passa sozinho.
    """
    apertar_rate_limit("RATE_LIMIT_REGISTER", "1/minute")

    primeira = await client.post(
        "/api/auth/register",
        json={"email": "limite1@sinalibras.dev", "name": "X", "password": SENHA},
    )
    assert primeira.status_code == 201, primeira.text

    bloqueada = await client.post(
        "/api/auth/register",
        json={"email": "limite2@sinalibras.dev", "name": "Y", "password": SENHA},
    )
    assert bloqueada.status_code == 429
    detail = bloqueada.json()["detail"]
    assert detail["code"] == "rate_limited"
    assert "tentativas" in detail["message"]
