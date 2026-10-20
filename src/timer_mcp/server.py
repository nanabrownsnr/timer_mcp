"""FastMCP application factory for Timer MCP.

Composes and exposes the FastMCP ASGI application.
Register new tools/resources in twynity.py.
"""

import logging
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from timer_mcp.config import settings
from timer_mcp.tools import register_tool
from timer_mcp.twynity import register_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server):
    """Application lifespan handler."""
    logger.info("Timer MCP starting up")
    yield
    logger.info("Timer MCP shutting down")


mcp = FastMCP(
    settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=app_lifespan,
)

register_routes(mcp)
register_tool(mcp)

# CORS middleware
match settings.ENVIRONMENT:
    case "development":
        origins = ["*"]
    case "production":
        origins = ["*"]
    case _:
        origins = ["*"]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = mcp.http_app(middleware=middleware)
