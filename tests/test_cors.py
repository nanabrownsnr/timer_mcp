"""Tests for CORS middleware on Timer MCP endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from timer_mcp.server import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCORSMiddleware:
    """Verify CORS headers on all endpoints."""

    @pytest.mark.asyncio
    async def test_health_has_cors(self, client):
        resp = await client.get("/api/v1/health", headers={"Origin": "https://example.com"})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_manifest_has_cors(self, client):
        resp = await client.get("/api/v1/.well-known/mcp.json", headers={"Origin": "https://example.com"})
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_preflight(self, client):
        resp = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp.headers
