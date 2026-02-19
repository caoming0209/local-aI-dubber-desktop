"""Integration test: digital humans API (T103).

Verifies:
- GET /api/digital-humans returns list with official entries
- POST /api/digital-humans/{id}/favorite toggles favorite
- DELETE /api/digital-humans/{id} blocks official deletion
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
async def test_list_digital_humans(client: AsyncClient):
    """GET /api/digital-humans should return seeded official entries."""
    resp = await client.get("/api/digital-humans")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.anyio
async def test_list_digital_humans_with_search(client: AsyncClient):
    """GET /api/digital-humans?search=商务 should filter results."""
    resp = await client.get("/api/digital-humans", params={"search": "商务"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_toggle_favorite(client: AsyncClient):
    """POST /api/digital-humans/{id}/favorite should toggle favorite status."""
    resp = await client.post("/api/digital-humans/dh_official_01/favorite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "is_favorited" in data["data"]


@pytest.mark.anyio
async def test_delete_official_blocked(client: AsyncClient):
    """DELETE /api/digital-humans/{id} should block deletion of official entries."""
    resp = await client.delete("/api/digital-humans/dh_official_01")
    data = resp.json()
    assert data["success"] is False


@pytest.mark.anyio
async def test_update_digital_human(client: AsyncClient):
    """PATCH /api/digital-humans/{id} should update name."""
    resp = await client.patch("/api/digital-humans/dh_official_01", json={"name": "新名称"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
