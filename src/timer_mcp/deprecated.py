"""Main entry point for Timer MCP server.

Run with:
    uvicorn timer_mcp.main:app --host 0.0.0.0 --port 8000
or:
    python -m timer_mcp.main
"""

import os
import sys

import uvicorn


def run_server() -> None:
    """Run the Timer MCP server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    uvicorn.run(
        "timer_mcp.server:app",
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run_server()
