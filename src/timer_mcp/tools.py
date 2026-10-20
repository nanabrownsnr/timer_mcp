"""Timer MCP tools for scheduling delayed execution.

Exposes the MCP tool definition and handler for the schedule_wait tool.
"""

import logging
from typing import Any

from timer_mcp.duration import parse_duration_to_seconds
from timer_mcp.models import DurationSchema, ScheduleRequest, ScheduleResponse
from timer_mcp.scheduler import create_job

logger = logging.getLogger(__name__)

# Base URL for status polling - can be overridden via environment
STATUS_BASE_URL = "/status"


def get_tool_definition() -> dict[str, Any]:
    """Return the MCP tool definition for schedule_wait.

    This defines the tool schema that MCP clients will see, including
    the JSON schema for duration parsing with granular fields.
    """
    return {
        "name": "schedule_wait",
        "description": (
            "Schedule a delayed execution (timer). Accepts a duration with "
            "granular fields (seconds, minutes, hours, days) and an optional "
            "callback action name. Returns a job ID and status URL for polling."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "object",
                    "description": "Duration specification with at least one non-zero field",
                    "properties": {
                        "seconds": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Seconds (0-86399+)",
                        },
                        "minutes": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Minutes (0-59+)",
                        },
                        "hours": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Hours (0-23+)",
                        },
                        "days": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Days (0-364+)",
                        },
                    },
                    "minProperties": 1,
                },
                "callback_action": {
                    "type": "string",
                    "default": "timer_expired",
                    "description": "Name/description of the callback to execute when the timer expires",
                },
            },
            "required": ["duration"],
            "additionalProperties": False,
        },
    }


async def handle_schedule_wait(params: dict[str, Any]) -> dict[str, Any]:
    """Handle the schedule_wait tool invocation.

    Args:
        params: The tool parameters containing 'duration' and optionally 'callback_action'.

    Returns:
        Dict with job_id, status, duration_seconds, scheduled_at, status_url, and message.

    Raises:
        ValueError: If the duration is invalid.
    """
    duration_data = params.get("duration", {})

    if not duration_data:
        raise ValueError("Duration must be provided with at least one field")

    # Build DurationSchema from the input
    duration = DurationSchema(
        seconds=duration_data.get("seconds"),
        minutes=duration_data.get("minutes"),
        hours=duration_data.get("hours"),
        days=duration_data.get("days"),
    )

    callback_action = params.get("callback_action", "timer_expired")

    # Parse duration to total seconds
    total_seconds = duration.to_seconds()
    if total_seconds is None:
        raise ValueError("Duration must specify at least one field")

    # Create the job
    job = await create_job(
        duration_seconds=total_seconds,
        callback_action=callback_action,
    )

    return ScheduleResponse(
        job_id=job.job_id,
        status=job.status.value,
        duration_seconds=total_seconds,
        scheduled_at=job.scheduled_at.isoformat(),
        status_url=f"{STATUS_BASE_URL}/{job.job_id}",
        message=f"Timer scheduled for {duration}. Job ID: {job.job_id}",
    ).model_dump()
