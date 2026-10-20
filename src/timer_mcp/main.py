"""FastAPI application factory for Timer MCP."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from timer_mcp.routes import router as timer_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Sets up and tears down resources when the application starts/stops.
    """
    logger.info("Timer MCP starting up")
    yield
    logger.info("Timer MCP shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Timer MCP",
        description="Timer MCP - Unauthenticated Twynity MCP for scheduling waits and delayed callbacks",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(timer_router, prefix="/api/v1")

    return app


app = create_app()
