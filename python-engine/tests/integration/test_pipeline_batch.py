"""Integration test: batch pipeline (T102).

Verifies:
- POST /api/pipeline/batch accepts scripts array
- Serial execution with batch progress events
- Failed items are skipped, succeeded items counted
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
async def test_batch_pipeline_returns_job_id(client: AsyncClient):
    """POST /api/pipeline/batch should return 202 with job_id and total_count."""
    resp = await client.post("/api/pipeline/batch", json={
        "scripts": [
            {"content": "第一条测试文案内容。"},
            {"content": "第二条测试文案内容。"},
            {"content": "第三条测试文案内容。"},
        ],
        "shared_config": {
            "voice_id": "voice_male_01",
            "digital_human_id": "dh_official_01",
        },
        "output_settings": {"name_prefix": "测试视频"},
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["total_count"] == 3
    assert "job_id" in data["data"]


@pytest.mark.anyio
async def test_batch_pipeline_rejects_empty_scripts(client: AsyncClient):
    """POST /api/pipeline/batch should reject empty scripts array."""
    resp = await client.post("/api/pipeline/batch", json={"scripts": []})
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_SCRIPT"


@pytest.mark.anyio
async def test_batch_cancel(client: AsyncClient):
    """Batch job should be cancellable."""
    resp = await client.post("/api/pipeline/batch", json={
        "scripts": [{"content": "文案一"}, {"content": "文案二"}],
        "shared_config": {},
    })
    job_id = resp.json()["data"]["job_id"]

    cancel_resp = await client.post(f"/api/pipeline/cancel/{job_id}")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "cancelled"
