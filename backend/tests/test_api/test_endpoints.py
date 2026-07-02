import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_health_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAnalysisEndpoints:
    @pytest.mark.anyio
    async def test_start_analysis_returns_202(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 365},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "thread_id" in data
        assert data["status"] == "pending"

    @pytest.mark.anyio
    async def test_start_analysis_default_values(self, client):
        resp = await client.post("/api/analysis", json={})
        assert resp.status_code == 202

    @pytest.mark.anyio
    async def test_start_analysis_invalid_days(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 5},
        )
        assert resp.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_start_analysis_days_too_high(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 1000},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_get_analysis_not_found(self, client):
        resp = await client.get("/api/analysis/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_get_analysis_after_start(self, client):
        # Start an analysis
        start_resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 365},
        )
        thread_id = start_resp.json()["thread_id"]

        # Poll for status
        status_resp = await client.get(f"/api/analysis/{thread_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["thread_id"] == thread_id
        assert data["status"] == "pending"

    @pytest.mark.anyio
    async def test_stream_unknown_thread_returns_404(self, client):
        resp = await client.get("/api/analysis/nonexistent-id/stream")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_stream_running_job_returns_409(self, client):
        from app.services.job_manager import job_manager

        start_resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 30},
        )
        thread_id = start_resp.json()["thread_id"]
        job_manager.update(thread_id, status="running")

        resp = await client.get(f"/api/analysis/{thread_id}/stream")
        assert resp.status_code == 409
