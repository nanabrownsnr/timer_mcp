"""Tests for callback execution and tools module."""

import pytest
from httpx import AsyncClient, ASGITransport

from timer_mcp.models import DurationSchema
from timer_mcp.scheduler import _jobs, list_jobs
from timer_mcp.tools import get_tool_definition, handle_schedule_wait


@pytest.fixture(autouse=True)
def clear_scheduler():
    """Clear scheduler state before each test."""
    _jobs.clear()
    yield
    _jobs.clear()


class TestToolDefinition:
    """Tests for the MCP tool definition."""

    def test_tool_exists(self):
        tool = get_tool_definition()
        assert tool["name"] == "schedule_wait"
        assert "description" in tool
        assert "inputSchema" in tool

    def test_tool_schema_properties(self):
        tool = get_tool_definition()
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "duration" in schema["properties"]
        assert "required" in schema
        assert "duration" in schema["required"]

    def test_duration_schema_fields(self):
        tool = get_tool_definition()
        duration_schema = tool["inputSchema"]["properties"]["duration"]
        assert "seconds" in duration_schema["properties"]
        assert "minutes" in duration_schema["properties"]
        assert "hours" in duration_schema["properties"]
        assert "days" in duration_schema["properties"]


class TestHandleScheduleWait:
    """Tests for the schedule_wait tool handler."""

    @pytest.mark.asyncio
    async def test_schedule_wait_basic(self):
        result = await handle_schedule_wait({
            "duration": {"seconds": 30},
        })
        assert "job_id" in result
        assert result["status"] == "pending"
        assert result["duration_seconds"] == 30
        assert "status_url" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_schedule_wait_with_callback(self):
        result = await handle_schedule_wait({
            "duration": {"minutes": 5},
            "callback_action": "notify_user",
        })
        assert result["duration_seconds"] == 300
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_schedule_wait_combined_duration(self):
        result = await handle_schedule_wait({
            "duration": {"hours": 1, "minutes": 30},
        })
        assert result["duration_seconds"] == 5400  # 1.5 hours

    @pytest.mark.asyncio
    async def test_schedule_wait_empty_duration(self):
        with pytest.raises(ValueError, match="Duration must be provided"):
            await handle_schedule_wait({})

    @pytest.mark.asyncio
    async def test_schedule_wait_null_duration(self):
        with pytest.raises(ValueError, match="Duration must be provided"):
            await handle_schedule_wait({"duration": None})

    @pytest.mark.asyncio
    async def test_schedule_wait_zero_duration(self):
        result = await handle_schedule_wait({
            "duration": {"seconds": 0},
        })
        assert result["duration_seconds"] == 0


class TestModels:
    """Tests for Pydantic models."""

    def test_duration_schema_single_field(self):
        d = DurationSchema(seconds=30)
        assert d.to_seconds() == 30

    def test_duration_schema_combined(self):
        d = DurationSchema(days=1, hours=2, minutes=30, seconds=15)
        assert d.to_seconds() == 95415

    def test_duration_schema_all_none(self):
        with pytest.raises(ValueError, match="At least one duration field"):
            DurationSchema()

    def test_duration_schema_negative(self):
        with pytest.raises(ValueError):
            DurationSchema(seconds=-1)

    def test_duration_schema_max_exceeded(self):
        with pytest.raises(ValueError, match="Maximum duration"):
            DurationSchema(days=366)

    def test_duration_str(self):
        d = DurationSchema(hours=1, minutes=30)
        assert "1h" in str(d)
        assert "30m" in str(d)

    def test_duration_str_zero(self):
        d = DurationSchema(seconds=0)
        assert str(d) == "0s"


class TestIntegration:
    """Integration tests for the full API."""

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
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_manifest_endpoint(self, client):
        resp = await client.get("/api/v1/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Timer MCP"
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "schedule_wait"

    @pytest.mark.asyncio
    async def test_mcp_endpoint_tools_list(self, client):
        resp = await client.post("/api/v1/mcp", json={"method": "tools/list"})
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data

    @pytest.mark.asyncio
    async def test_mcp_endpoint_schedule_wait(self, client):
        resp = await client.post("/api/v1/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "schedule_wait",
                "arguments": {
                    "duration": {"seconds": 1},
                    "callback_action": "test_action",
                },
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["duration_seconds"] == 1

    @pytest.mark.asyncio
    async def test_mcp_endpoint_unknown_tool(self, client):
        resp = await client.post("/api/v1/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {},
            },
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_mcp_endpoint_unknown_method(self, client):
        resp = await client.post("/api/v1/mcp", json={
            "method": "unknown/method",
            "params": {},
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_status_endpoint_not_found(self, client):
        resp = await client.get("/api/v1/status/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_status_endpoint_with_job(self, client):
        schedule_resp = await client.post("/api/v1/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "schedule_wait",
                "arguments": {
                    "duration": {"seconds": 1},
                },
            },
        })
        job_id = schedule_resp.json()["job_id"]

        status_resp = await client.get(f"/api/v1/status/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("pending", "running", "completed")

    @pytest.mark.asyncio
    async def test_jobs_list_endpoint(self, client):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_delete_job_endpoint(self, client):
        schedule_resp = await client.post("/api/v1/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "schedule_wait",
                "arguments": {
                    "duration": {"minutes": 30},
                },
            },
        })
        job_id = schedule_resp.json()["job_id"]

        delete_resp = await client.delete(f"/api/v1/status/{job_id}")
        assert delete_resp.status_code == 200
        data = delete_resp.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_job(self, client):
        resp = await client.delete("/api/v1/status/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_schedule_wait_invalid_duration(self, client):
        resp = await client.post("/api/v1/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "schedule_wait",
                "arguments": {
                    "duration": {},
                },
            },
        })
        assert resp.status_code == 400
