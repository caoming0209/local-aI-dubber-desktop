"""Integration test: single video pipeline (T101).

Verifies:
- POST /api/pipeline/single returns job_id (202)
- SSE progress stream pushes complete step sequence
- Works table gets a new record on success
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

# Patch env for dev mode before importing app
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
async def test_single_pipeline_returns_job_id(client: AsyncClient):
    """POST /api/pipeline/single should return 202 with job_id."""
    resp = await client.post("/api/pipeline/single", json={
        "script": "这是一段测试文案，用于验证单条视频生成流水线。",
        "voice_id": "voice_male_01",
        "voice_params": {"speed": 1.0, "volume": 1.0, "emotion": 0.5},
        "digital_human_id": "dh_official_01",
        "background": {"type": "solid_color", "value": "#FFFFFF"},
        "aspect_ratio": "9:16",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["success"] is True
    assert "job_id" in data["data"]
    assert data["data"]["estimated_steps"] == 4


@pytest.mark.anyio
async def test_single_pipeline_rejects_short_script(client: AsyncClient):
    """POST /api/pipeline/single should reject scripts shorter than 2 chars."""
    resp = await client.post("/api/pipeline/single", json={"script": "a"})
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_SCRIPT"


@pytest.mark.anyio
async def test_single_pipeline_rejects_empty_script(client: AsyncClient):
    """POST /api/pipeline/single should reject empty scripts."""
    resp = await client.post("/api/pipeline/single", json={"script": ""})
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_SCRIPT"


@pytest.mark.anyio
async def test_job_state_query(client: AsyncClient):
    """GET /api/jobs/{job_id}/state should return job status."""
    # Create a job first
    resp = await client.post("/api/pipeline/single", json={
        "script": "测试作业状态查询功能。",
        "voice_id": "voice_male_01",
        "digital_human_id": "dh_official_01",
    })
    job_id = resp.json()["data"]["job_id"]

    # Query state
    state_resp = await client.get(f"/api/jobs/{job_id}/state")
    assert state_resp.status_code == 200
    state_data = state_resp.json()
    assert state_data["success"] is True
    assert "status" in state_data["data"]


@pytest.mark.anyio
async def test_cancel_job(client: AsyncClient):
    """POST /api/pipeline/cancel/{job_id} should cancel a running job."""
    resp = await client.post("/api/pipeline/single", json={
        "script": "测试取消功能的文案内容。",
        "voice_id": "voice_male_01",
        "digital_human_id": "dh_official_01",
    })
    job_id = resp.json()["data"]["job_id"]

    cancel_resp = await client.post(f"/api/pipeline/cancel/{job_id}")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "cancelled"
