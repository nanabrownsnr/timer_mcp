"""Register health and manifest HTTP routes for Timer MCP."""

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
        })

    @mcp.custom_route("/api/v1/.well-known/mcp.json", methods=["GET"])
    async def manifest(request: Request) -> JSONResponse:
        """MCP service manifest."""
        return JSONResponse({
            "name": "Timer MCP",
            "version": "1.0.0",
            "description": "Timer MCP — wait for a specified duration",
        })
