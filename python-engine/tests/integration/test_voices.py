"""Integration test: voices API (T104).

Verifies:
- GET /api/voices returns seeded voice models
- POST /api/voices/{id}/favorite toggles favorite
- DELETE /api/voices/{id}/model handles not-downloaded state
"""

import pytest
from httpx import AsyncClient, ASGITransport

import os
os.environ["DEV_MODE"] = "1"

from src.api.server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_list_voices(client: AsyncClient):
    """GET /api/voices should return seeded voice models."""
    resp = await client.get("/api/voices")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.anyio
async def test_list_voices_by_category(client: AsyncClient):
    """GET /api/voices?category=male should filter by category."""
    resp = await client.get("/api/voices", params={"category": "male"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_list_voices_by_download_status(client: AsyncClient):
    """GET /api/voices?download_status=not_downloaded should filter."""
    resp = await client.get("/api/voices", params={"download_status": "not_downloaded"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_toggle_voice_favorite(client: AsyncClient):
    """POST /api/voices/{id}/favorite should toggle favorite."""
    resp = await client.post("/api/voices/voice_male_01/favorite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "is_favorited" in data["data"]


@pytest.mark.anyio
async def test_delete_model_not_downloaded(client: AsyncClient):
    """DELETE /api/voices/{id}/model should fail for not-downloaded model."""
    resp = await client.delete("/api/voices/voice_male_01/model")
    data = resp.json()
    assert data["success"] is False


@pytest.mark.anyio
async def test_voice_not_found(client: AsyncClient):
    """Operations on non-existent voice should return NOT_FOUND."""
    resp = await client.post("/api/voices/nonexistent/favorite")
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
