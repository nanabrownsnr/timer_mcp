"""Register Twynity's well-known manifest and health HTTP routes.

FastMCP's tool registry handles tool calls; custom HTTP routes for
health, manifest, and job management are registered here via @mcp.custom_route.
"""

from urllib.parse import urlparse

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse


def register_routes(mcp: FastMCP):
    @mcp.custom_route("/api/v1/health", methods=["GET"])
    async def health_status(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "service": "Timer MCP",
            "version": "1.0.0",
            "uptime_seconds": 0,
        })

    @mcp.custom_route("/api/v1/.well-known/mcp.json", methods=["GET"])
    async def manifest(request: Request) -> JSONResponse:
        """MCP service manifest."""
        return JSONResponse({
            "name": "Timer MCP",
            "version": "1.0.0",
            "description": "Timer MCP - Schedule delayed execution with granular duration support",
            "mcp_version": "2024-11-05",
        })

    @mcp.custom_route("/api/v1/manifest", methods=["GET"])
    async def manifest_alt(request: Request) -> JSONResponse:
        """Alternative manifest endpoint (legacy path)."""
        return JSONResponse({
            "name": "Timer MCP",
            "version": "1.0.0",
            "description": "Timer MCP - Schedule delayed execution with granular duration support",
            "mcp_version": "2024-11-05",
        })

    @mcp.custom_route("/api/v1/status/{job_id}", methods=["GET"])
    async def get_status(request: Request) -> JSONResponse:
        """Get the status of a scheduled job."""
        from timer_mcp.scheduler import get_job_status
        # Extract job_id from the request path
        path = request.url.path
        job_id = path.rsplit("/", 1)[-1]
        status = await get_job_status(job_id)
        if status is None:
            return JSONResponse(
                {"detail": f"Job not found: {job_id}"},
                status_code=404,
            )
        return JSONResponse(status.model_dump())

    @mcp.custom_route("/api/v1/status/{job_id}", methods=["DELETE"])
    async def delete_job(request: Request) -> JSONResponse:
        """Cancel a scheduled job."""
        from timer_mcp.scheduler import cancel_job
        path = request.url.path
        job_id = path.rsplit("/", 1)[-1]
        cancelled = await cancel_job(job_id)
        if not cancelled:
            return JSONResponse(
                {"detail": f"Job not found or already completed: {job_id}"},
                status_code=404,
            )
        return JSONResponse({"job_id": job_id, "status": "cancelled"})

    @mcp.custom_route("/api/v1/jobs", methods=["GET"])
    async def list_jobs_endpoint(request: Request) -> JSONResponse:
        """List all scheduled jobs."""
        from timer_mcp.scheduler import list_jobs
        jobs = await list_jobs()
        return JSONResponse([j.model_dump() for j in jobs])
