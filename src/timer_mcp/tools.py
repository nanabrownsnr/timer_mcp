"""Timer MCP tools for scheduling delayed execution.

Uses FastMCP's @mcp.tool() decorator — no manual POST /mcp routing needed.
"""

import logging
from typing import Any, Optional

from fastmcp import FastMCP

from timer_mcp.duration import parse_duration_to_seconds
from timer_mcp.scheduler import create_job

logger = logging.getLogger(__name__)

# Base URL for status polling
STATUS_BASE_URL = "/status"


def register_tool(mcp: FastMCP):
    """Register the schedule_wait tool on the given FastMCP instance."""

    @mcp.tool()
    async def schedule_wait(
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        callback_action: str = "timer_expired",
    ) -> dict[str, Any]:
        """Schedule a delayed execution (timer).

        Accepts a duration with granular fields (seconds, minutes, hours, days)
        and an optional callback action name. Returns a job ID and status URL for polling.

        Args:
            seconds: Seconds component (0-86399+)
            minutes: Minutes component (0-59+)
            hours: Hours component (0-23+)
            days: Days component (0-364+)
            callback_action: Name/description of the callback to execute when the timer expires

        Returns:
            Dict with job_id, status, duration_seconds, scheduled_at, status_url, and message.

        Raises:
            ValueError: If the duration is invalid.
        """
        total_seconds = parse_duration_to_seconds(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days,
        )

        # Create the job
        job = await create_job(
            duration_seconds=total_seconds,
            callback_action=callback_action,
        )

        parts = []
        if days and days > 0:
            parts.append(f"{days}d")
        if hours and hours > 0:
            parts.append(f"{hours}h")
        if minutes and minutes > 0:
            parts.append(f"{minutes}m")
        if seconds and seconds > 0:
            parts.append(f"{seconds}s")
        duration_str = " ".join(parts) if parts else "0s"

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "duration_seconds": total_seconds,
            "scheduled_at": job.scheduled_at.isoformat(),
            "status_url": f"{STATUS_BASE_URL}/{job.job_id}",
            "message": f"Timer scheduled for {duration_str}. Job ID: {job.job_id}",
        }
