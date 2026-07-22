"""
Test bootstrap.

Strategy:
  - Override env vars BEFORE app imports so pydantic-settings picks up
    the test values (different DB, in-test JWT secret, gigantic rate limits).
  - One session-scoped Mongo connection: drop the test DB at start,
    ensure_indexes, seed a minimal catalog.
  - Autouse function fixture wipes mutable collections (users / progress)
    between tests so each test starts from a clean slate without paying
    for re-seeding the content catalog.
  - httpx AsyncClient with ASGITransport runs FastAPI in-process — no
    port, no live server, fast.
"""

from __future__ import annotations

import os

# --- env override (must happen before any `from app...` import) ------------
# DB_NAME and rate limits are FORCED (not setdefault) so that running tests
# inside the dev `backend` container — which has those vars pre-set — never
# touches the dev database or trips production rate limits.
os.environ["DB_NAME"] = "sinalibras_test"
os.environ["RATE_LIMIT_LOGIN"] = "10000/minute"
os.environ["RATE_LIMIT_REGISTER"] = "10000/minute"
os.environ["RATE_LIMIT_REFRESH"] = "10000/minute"
# These can inherit from the environment when present (Docker / CI), else fall
# back to local defaults for `pytest` ran outside a container.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET", "test-secret-must-be-at-least-32-characters-long")
os.environ.setdefault("CORS_ORIGINS", "http://test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.mongo import (  # noqa: E402
    close_mongo_connection,
    connect_to_mongo,
    ensure_indexes,
)
from app.main import create_app  # noqa: E402
from app.models.lesson import Lesson  # noqa: E402
from app.models.phase import Phase  # noqa: E402
from app.models.sign import Sign  # noqa: E402


# ---------------------------------------------------------------------------
# Session bootstrap
# ---------------------------------------------------------------------------

CATALOG = [
    {
        "order": 1, "title": "Cumprimentos", "description": "Demo",
        "lessons": [
            {"order": 1, "title": "Olá e Tchau", "xp_reward": 20,
             "signs": ["Olá", "Tchau", "Tudo bem?", "Obrigado"]},
            {"order": 2, "title": "Bom dia", "xp_reward": 25,
             "signs": ["Bom dia", "Boa tarde", "Boa noite", "Até logo"]},
        ],
    },
    {
        "order": 2, "title": "Família", "description": "Demo",
        "lessons": [
            {"order": 1, "title": "Pais", "xp_reward": 25,
             "signs": ["Pai", "Mãe", "Filho", "Filha"]},
        ],
    },
]


async def _seed(db) -> None:
    for phase_def in CATALOG:
        phase = Phase(title=phase_def["title"], description=phase_def["description"], order=phase_def["order"])
        await db.phases.insert_one(phase.to_mongo())
        for lesson_def in phase_def["lessons"]:
            sign_ids = []
            for term in lesson_def["signs"]:
                sign = Sign(portuguese_term=term, text_description=f"Sinal {term}")
                await db.signs.insert_one(sign.to_mongo())
                sign_ids.append(sign.id)
            lesson = Lesson(
                phase_id=phase.id,
                title=lesson_def["title"],
                order=lesson_def["order"],
                xp_reward=lesson_def["xp_reward"],
                sign_ids=sign_ids,
            )
            await db.lessons.insert_one(lesson.to_mongo())


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _db_session():
    """Connect once, drop the test DB, seed, tear down at session end."""
    settings = get_settings()
    bootstrap_client = AsyncIOMotorClient(settings.MONGO_URL)
    await bootstrap_client.drop_database(settings.DB_NAME)
    bootstrap_client.close()

    db = await connect_to_mongo(settings)
    await ensure_indexes(db)
    await _seed(db)
    yield db
    await close_mongo_connection()


@pytest_asyncio.fixture(autouse=True)
async def _clean_mutable_state():
    """Reset per-user state between tests. Catalog (phases/lessons/signs) survives."""
    yield
    # Late import: by now the lifespan has run via _db_session.
    from app.db.mongo import get_db
    db = get_db()
    await db.users.delete_many({})
    await db.progress.delete_many({})


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def apertar_rate_limit(monkeypatch):
    """
    Baixa um RATE_LIMIT_* para o teste que precisa VER o 429.

    Os limites deste arquivo são gigantes de propósito, senão a suíte inteira
    esbarraria neles. O limiter lê o valor por request (`lambda:
    get_settings()...`), então basta trocar a env var e limpar o cache —
    inclusive na volta, ou o limite apertado vazaria para os outros testes.
    """
    def aplicar(nome: str, valor: str) -> None:
        monkeypatch.setenv(nome, valor)
        get_settings.cache_clear()

    yield aplicar
    monkeypatch.undo()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def auth_client(client) -> AsyncClient:
    """Client logged in as a freshly-created user. Cookies are persisted on the client."""
    r = await client.post(
        "/api/auth/register",
        json={"email": "tester@example.com", "name": "Tester", "password": "supersecret"},
    )
    assert r.status_code == 201, r.text
    return client
