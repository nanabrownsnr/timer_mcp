"""Main entry point for Timer MCP server.

Run with:
    uvicorn timer_mcp.server:app --host 0.0.0.0 --port 8000
or:
    python -m timer_mcp.main
"""

import os
import sys

import uvicorn
from timer_mcp.config import settings


def run_server() -> None:
    """Run the Timer MCP server."""
    uvicorn.run(
        "timer_mcp.server:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run_server()
