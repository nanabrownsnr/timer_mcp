"""Timer MCP tools for scheduling delayed execution."""

import asyncio
import logging
from typing import Any, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_tool(mcp: FastMCP):
    """Register the wait tool on the given FastMCP instance."""

    @mcp.tool()
    async def wait(
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
    ) -> dict[str, Any]:
        """Wait for a specified duration and then return.

        Accepts granular time units. At least one must be greater than zero.
        The tool blocks until the full duration has elapsed, then returns
        the total seconds waited.

        Args:
            seconds: Seconds to wait (0-86399+)
            minutes: Minutes to wait (0-59+)
            hours: Hours to wait (0-23+)
            days: Days to wait (0-364+)

        Returns:
            Dict with total_seconds waited and a confirmation message.

        Raises:
            ValueError: If no time units are provided or any value is negative.
            TypeError: If any value is not an integer.
        """
        total = (
            (days * 86400)
            + (hours * 3600)
            + (minutes * 60)
            + seconds
        )

        if total <= 0:
            raise ValueError("At least one duration field must be greater than zero")

        logger.info("Waiting %ds...", total)
        await asyncio.sleep(total)
        logger.info("Wait complete: %ds", total)

        return {
            "total_seconds": total,
            "message": f"Waited for {total} seconds.",
        }
