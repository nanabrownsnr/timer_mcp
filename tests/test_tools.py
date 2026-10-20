"""Tests for the wait tool."""

import pytest
from fastmcp import FastMCP


class TestToolRegistration:
    """Tests that the tool is registered on FastMCP."""

    @pytest.mark.asyncio
    async def test_wait_tool_is_registered(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "wait" in tool_names

    @pytest.mark.asyncio
    async def test_wait_tool_has_description(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        tools = await mcp.list_tools()
        wait_tool = [t for t in tools if t.name == "wait"][0]
        assert wait_tool.description
        assert "wait" in wait_tool.description.lower()


class TestWaitTool:
    """Tests for the wait tool functionality."""

    @pytest.mark.asyncio
    async def test_wait_seconds(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        result = await mcp.call_tool("wait", {"seconds": 1})
        assert result.structured_content["total_seconds"] == 1
        assert "seconds" in result.structured_content["message"].lower()

    @pytest.mark.asyncio
    async def test_wait_zero_raises(self):
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        with pytest.raises(Exception, match="greater than zero"):
            await mcp.call_tool("wait", {"seconds": 0})

    @pytest.mark.asyncio
    async def test_wait_all_zero_raises(self):
        """All-zero fields should raise."""
        mcp = FastMCP("test")
        from timer_mcp.tools import register_tool
        register_tool(mcp)
        with pytest.raises(Exception, match="greater than zero"):
            await mcp.call_tool("wait", {"hours": 0, "minutes": 0})
