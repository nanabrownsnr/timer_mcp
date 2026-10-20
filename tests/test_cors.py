"""Tests for CORS middleware on Timer MCP endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from timer_mcp.server import app

TEST_ORIGIN = "https://example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCORSMiddleware:
    """Tests to verify CORS headers are present on all endpoints."""

    @pytest.mark.asyncio
    async def test_health_has_cors_headers(self, client):
        """CORS headers should be present on /health responses when Origin is sent."""
        resp = await client.get("/api/v1/health", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_manifest_has_cors_headers(self, client):
        """CORS headers should be present on /manifest responses when Origin is sent."""
        resp = await client.get("/api/v1/manifest", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_mcp_post_has_cors_headers(self, client):
        """CORS headers should be present on POST /mcp responses when Origin is sent."""
        resp = await client.post(
            "/api/v1/mcp", json={"method": "tools/list"}, headers={"Origin": TEST_ORIGIN}
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_mcp_cors_with_different_origin(self, client):
        """CORS headers should work with different origins."""
        resp = await client.post(
            "/api/v1/mcp",
            json={"method": "tools/list"},
            headers={"Origin": "https://other-domain.io"},
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_mcp_schedule_wait_has_cors_headers(self, client):
        """CORS headers should be present on actual tool invocation when Origin is sent."""
        resp = await client.post(
            "/api/v1/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "schedule_wait",
                    "arguments": {"duration": {"seconds": 1}},
                },
            },
            headers={"Origin": TEST_ORIGIN},
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_options_preflight_cors(self, client):
        """OPTIONS preflight requests should return CORS headers with allow-methods."""
        resp = await client.options(
            "/api/v1/mcp",
            headers={
                "Origin": TEST_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.status_code == 200
        # Preflight includes CORS headers for methods and credentials
        assert "access-control-allow-origin" in resp.headers
        assert resp.headers["access-control-allow-credentials"] == "true"
        assert "access-control-allow-methods" in resp.headers

    @pytest.mark.asyncio
    async def test_status_endpoint_has_cors_headers(self, client):
        """CORS headers should be present on /status/{job_id} responses when Origin is sent."""
        schedule_resp = await client.post(
            "/api/v1/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "schedule_wait",
                    "arguments": {"duration": {"minutes": 30}},
                },
            },
            headers={"Origin": TEST_ORIGIN},
        )
        job_id = schedule_resp.json()["job_id"]

        resp = await client.get(
            f"/api/v1/status/{job_id}", headers={"Origin": TEST_ORIGIN}
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_jobs_list_has_cors_headers(self, client):
        """CORS headers should be present on /jobs responses when Origin is sent."""
        resp = await client.get("/api/v1/jobs", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_delete_job_has_cors_headers(self, client):
        """CORS headers should be present on DELETE /status/{job_id} responses when Origin is sent."""
        schedule_resp = await client.post(
            "/api/v1/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "schedule_wait",
                    "arguments": {"duration": {"minutes": 30}},
                },
            },
            headers={"Origin": TEST_ORIGIN},
        )
        job_id = schedule_resp.json()["job_id"]

        resp = await client.delete(
            f"/api/v1/status/{job_id}", headers={"Origin": TEST_ORIGIN}
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert resp.headers["access-control-allow-credentials"] == "true"
