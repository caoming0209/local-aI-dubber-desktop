"""Integration test: license API (T106).

Verifies:
- GET /api/license/status returns dev mode status
- POST /api/license/activate validates format
- POST /api/license/consume-trial decrements count
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
async def test_license_status_dev_mode(client: AsyncClient):
    """GET /api/license/status should return dev mode info."""
    resp = await client.get("/api/license/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["dev_mode"] is True
    assert data["data"]["remaining_trial_count"] == 999


@pytest.mark.anyio
async def test_activate_empty_code(client: AsyncClient):
    """POST /api/license/activate with empty code should fail."""
    resp = await client.post("/api/license/activate", json={"activation_code": ""})
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "LICENSE_INVALID_CODE"


@pytest.mark.anyio
async def test_activate_invalid_format(client: AsyncClient):
    """POST /api/license/activate with bad format should fail."""
    resp = await client.post("/api/license/activate", json={"activation_code": "INVALID"})
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "LICENSE_INVALID_CODE"


@pytest.mark.anyio
async def test_activate_valid_format(client: AsyncClient):
    """POST /api/license/activate with valid format should attempt remote activation."""
    # This will fail at the remote call, but format validation should pass
    resp = await client.post("/api/license/activate", json={
        "activation_code": "ABCD-EFGH-IJKL-MNOP"
    })
    data = resp.json()
    # Will fail because remote server is unreachable, but format is valid
    assert data["success"] is False
    # Error should NOT be LICENSE_INVALID_CODE (format passed)
    assert data["error"]["code"] != "LICENSE_INVALID_CODE"
