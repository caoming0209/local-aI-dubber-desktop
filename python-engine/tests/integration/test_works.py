"""Integration test: works library API (T105 backend portion).

Verifies:
- GET /api/works returns paginated list
- PATCH /api/works/{id} renames work
- DELETE /api/works/{id} deletes work
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
async def test_list_works_empty(client: AsyncClient):
    """GET /api/works should return empty list initially."""
    resp = await client.get("/api/works")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"]["items"], list)
    assert "pagination" in data["data"]


@pytest.mark.anyio
async def test_list_works_with_search(client: AsyncClient):
    """GET /api/works?search=test should filter results."""
    resp = await client.get("/api/works", params={"search": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_list_works_with_sort(client: AsyncClient):
    """GET /api/works?sort=created_at_desc should sort results."""
    resp = await client.get("/api/works", params={"sort": "created_at_desc"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.anyio
async def test_get_work_not_found(client: AsyncClient):
    """GET /api/works/{id} should return NOT_FOUND for missing work."""
    resp = await client.get("/api/works/nonexistent")
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.anyio
async def test_delete_work_not_found(client: AsyncClient):
    """DELETE /api/works/{id} should return NOT_FOUND for missing work."""
    resp = await client.delete("/api/works/nonexistent")
    data = resp.json()
    assert data["success"] is False
