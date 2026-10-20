"""Tests for tools module."""

import pytest
from httpx import AsyncClient, ASGITransport
from fastmcp import FastMCP

from timer_mcp.scheduler import _jobs, list_jobs


@pytest.fixture(autouse=True)
def clear_scheduler():
    """Clear scheduler state before each test."""
    _jobs.clear()
    yield
    _jobs.clear()


class TestToolRegistration:
    """Tests for tool registration."""

    @pytest.mark.asyncio
    async def test_tool_is_registered(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "schedule_wait" in tool_names

    @pytest.mark.asyncio
    async def test_tool_description_exists(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        tools = await mcp.list_tools()
        schedule_wait = [t for t in tools if t.name == "schedule_wait"][0]
        assert schedule_wait.description
        assert "timer" in schedule_wait.description.lower() or "delayed" in schedule_wait.description.lower()


class TestHandleScheduleWait:
    """Tests for the schedule_wait tool via FastMCP."""

    @pytest.mark.asyncio
    async def test_schedule_wait_basic(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)

        result = await mcp.call_tool("schedule_wait", {"seconds": 30})
        data = result.structured_content
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["duration_seconds"] == 30
        assert "status_url" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_schedule_wait_with_callback(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)

        result = await mcp.call_tool("schedule_wait", {
            "minutes": 5,
            "callback_action": "notify_user",
        })
        data = result.structured_content
        assert data["duration_seconds"] == 300
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_schedule_wait_combined_duration(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)

        result = await mcp.call_tool("schedule_wait", {
            "hours": 1,
            "minutes": 30,
        })
        data = result.structured_content
        assert data["duration_seconds"] == 5400

    @pytest.mark.asyncio
    async def test_schedule_wait_zero_duration(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)

        result = await mcp.call_tool("schedule_wait", {
            "seconds": 0,
        })
        data = result.structured_content
        assert data["duration_seconds"] == 0

    @pytest.mark.asyncio
    async def test_schedule_wait_no_duration(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)

        with pytest.raises(Exception):
            await mcp.call_tool("schedule_wait", {})


class TestIntegration:
    """Integration tests for the full API via FastMCP's http_app."""

    @pytest.fixture
    async def client(self):
        from timer_mcp.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Timer MCP"

    @pytest.mark.asyncio
    async def test_manifest_endpoint(self, client):
        resp = await client.get("/api/v1/.well-known/mcp.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Timer MCP"

    @pytest.mark.asyncio
    async def test_legacy_manifest_endpoint(self, client):
        resp = await client.get("/api/v1/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Timer MCP"

    @pytest.mark.asyncio
    async def test_status_endpoint_not_found(self, client):
        resp = await client.get("/api/v1/status/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_jobs_list_endpoint(self, client):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
