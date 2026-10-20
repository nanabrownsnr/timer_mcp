"""Service identity and environment settings for Timer MCP."""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_ID: str = "timer_mcp"
    APP_TITLE: str = "Timer MCP"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development | staging | production
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: str = "*"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()


def configure_logging():
    """Set up file + console logging with rotation."""
    os.makedirs("./logs", exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.addHandler(console_handler)

    file_handler = TimedRotatingFileHandler(
        filename=f"./logs/timer_mcp.log",
        when="midnight",
        interval=1,
        backupCount=7,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)


configure_logging()
