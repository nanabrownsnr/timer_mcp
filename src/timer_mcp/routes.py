"""Health, manifest, and MCP endpoint routes for Timer MCP.

Provides the standard endpoints expected by the Twynity MCP framework:
- GET /health - Health check
- GET /manifest - MCP service manifest
- POST /mcp - MCP tool invocation endpoint
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from timer_mcp.models import (
    HealthResponse,
    ManifestResponse,
)
from timer_mcp.tools import get_tool_definition, handle_schedule_wait
from timer_mcp.scheduler import get_job_status, list_jobs, cancel_job

logger = logging.getLogger(__name__)

# Service metadata
SERVICE_NAME = "Timer MCP"
SERVICE_VERSION = "1.0.0"
MCP_VERSION = "2024-11-05"
_START_TIME = time.time()

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns the service health status, name, version, and uptime.
    """
    uptime = time.time() - _START_TIME
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=round(uptime, 2),
    )


@router.get("/manifest", response_model=ManifestResponse)
async def get_manifest() -> ManifestResponse:
    """MCP manifest endpoint.

    Returns the service manifest describing the MCP tools and endpoints.
    """
    tool_def = get_tool_definition()
    return ManifestResponse(
        name=SERVICE_NAME,
        version=SERVICE_VERSION,
        description="Timer MCP - Schedule delayed execution with granular duration support",
        mcp_version=MCP_VERSION,
        tools=[tool_def],
        endpoints=["/health", "/manifest", "/mcp", "/status/{job_id}", "/jobs"],
    )


@router.post("/mcp")
async def mcp_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    """MCP tool invocation endpoint.

    Receives tool invocations in MCP format and routes them to the
    appropriate handler. Currently supports:
    - schedule_wait: Schedule a delayed timer

    Args:
        body: The MCP request body containing 'method' and 'params'.

    Returns:
        The tool execution result.

    Raises:
        HTTPException: If the method is unknown or params are invalid.
    """
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_params = params.get("arguments", {})

        if tool_name == "schedule_wait":
            try:
                return await handle_schedule_wait(tool_params)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error("Error executing schedule_wait: %s", e)
                raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    elif method == "tools/list":
        return {"tools": [get_tool_definition()]}
    else:
        raise HTTPException(status_code=404, detail=f"Unknown MCP method: {method}")


@router.get("/status/{job_id}", response_model=dict)
async def get_status(job_id: str) -> dict[str, Any]:
    """Get the status of a scheduled job.

    Args:
        job_id: The job ID to look up.

    Returns:
        Job status response as a dict.

    Raises:
        HTTPException: If the job is not found.
    """
    status = await get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return status.model_dump()


@router.get("/jobs", response_model=list)
async def list_all_jobs() -> list[dict[str, Any]]:
    """List all scheduled jobs.

    Returns:
        List of all jobs as dicts.
    """
    jobs = await list_jobs()
    return [j.model_dump() for j in jobs]


@router.delete("/status/{job_id}", response_model=dict)
async def delete_job(job_id: str) -> dict[str, Any]:
    """Cancel a scheduled job.

    Args:
        job_id: The job ID to cancel.

    Returns:
        Result of the cancellation.

    Raises:
        HTTPException: If the job is not found.
    """
    cancelled = await cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Job not found or already completed: {job_id}")
    return {"job_id": job_id, "status": "cancelled"}
