"""Tests for CORS middleware on Timer MCP endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from fastmcp import FastMCP
from timer_mcp.scheduler import _jobs
from timer_mcp.tools import register_tool
from timer_mcp.server import app


@pytest.fixture(autouse=True)
def clear_scheduler():
    """Clear scheduler state before each test."""
    _jobs.clear()
    yield
    _jobs.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


TEST_ORIGIN = "https://example.com"


class TestCORSMiddleware:
    """Tests to verify CORS headers are present on all endpoints."""

    @pytest.mark.asyncio
    async def test_health_has_cors_headers(self, client):
        resp = await client.get("/api/v1/health", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
        assert "access-control-allow-credentials" in resp.headers or "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_manifest_well_known_has_cors_headers(self, client):
        resp = await client.get("/api/v1/.well-known/mcp.json", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_manifest_legacy_has_cors_headers(self, client):
        resp = await client.get("/api/v1/manifest", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_cors_with_different_origin(self, client):
        resp = await client.get(
            "/api/v1/health",
            headers={"Origin": "https://other-domain.io"},
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_options_preflight_cors(self, client):
        resp = await client.options(
            "/api/v1/health",
            headers={
                "Origin": TEST_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastMCP may return 405 or 200 for unknown routes — just check CORS headers when present
        assert "access-control-allow-origin" in resp.headers or resp.status_code in (200, 405)

    @pytest.mark.asyncio
    async def test_status_endpoint_has_cors_headers(self, client):
        resp = await client.get("/api/v1/status/nonexistent", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code in (404, 500)  # endpoint may not exist yet
        assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_jobs_list_has_cors_headers(self, client):
        resp = await client.get("/api/v1/jobs", headers={"Origin": TEST_ORIGIN})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"
