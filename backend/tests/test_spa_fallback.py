"""
SPA fallback behavior — exercised only when FRONTEND_BUILD_DIR is set
(i.e. the single-host prod deploy). The default test app skips this
branch, so we build a dedicated app here with a temp build dir.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def spa_build_dir(tmp_path: Path) -> Path:
    """Minimal fake SPA build dir — just an index.html and one asset."""
    (tmp_path / "index.html").write_text("<!doctype html><html><body>SPA</body></html>", encoding="utf-8")
    static = tmp_path / "static"
    static.mkdir()
    (static / "main.js").write_text("console.log('app');", encoding="utf-8")
    return tmp_path


@pytest_asyncio.fixture
async def spa_client(spa_build_dir):
    settings = Settings(FRONTEND_BUILD_DIR=str(spa_build_dir))
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_unmatched_api_path_returns_404_not_spa_html(spa_client):
    """Regression: the catch-all used to swallow /api/* typos and return
    index.html with HTTP 200, breaking axios callers that JSON.parse'd
    the response. Unknown /api/* must 404."""
    r = await spa_client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert "html" not in r.headers.get("content-type", "").lower()


async def test_unmatched_api_root_returns_404(spa_client):
    r = await spa_client.get("/api")
    assert r.status_code == 404


async def test_registered_api_route_still_works(spa_client):
    r = await spa_client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


async def test_spa_route_returns_index_html(spa_client):
    """An unknown non-/api path serves index.html so client-side routing works."""
    r = await spa_client.get("/lessons")
    assert r.status_code == 200
    assert "SPA" in r.text


async def test_existing_static_asset_served(spa_client):
    r = await spa_client.get("/static/main.js")
    assert r.status_code == 200
    assert "console.log" in r.text


async def test_missing_file_with_extension_returns_404(spa_client):
    r = await spa_client.get("/robots.txt")
    assert r.status_code == 404
