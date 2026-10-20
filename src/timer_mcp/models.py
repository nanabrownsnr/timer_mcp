"""Pydantic models for the Timer MCP."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TimeUnit(str, Enum):
    """Valid time units for duration specification."""

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class DurationSchema(BaseModel):
    """Duration specification with granular fields.

    At least one field must be provided. Values must be non-negative.
    Fields are optional but at least one must be non-None.
    """

    seconds: Optional[int] = Field(default=None, ge=0, description="Seconds component (0-59+)")
    minutes: Optional[int] = Field(default=None, ge=0, description="Minutes component (0-59+)")
    hours: Optional[int] = Field(default=None, ge=0, description="Hours component")
    days: Optional[int] = Field(default=None, ge=0, description="Days component")

    def model_post_init(self, __context) -> None:
        total = self.to_seconds()
        if total is None:
            raise ValueError("At least one duration field must be provided (seconds, minutes, hours, or days)")
        if total < 0:
            raise ValueError("Duration must be non-negative")
        if total > 86400 * 365:  # 1 year max
            raise ValueError("Maximum duration is 1 year (31536000 seconds)")

    def to_seconds(self) -> Optional[int]:
        """Convert all duration fields to total seconds."""
        if self.seconds is None and self.minutes is None and self.hours is None and self.days is None:
            return None
        total = 0
        if self.seconds is not None:
            total += self.seconds
        if self.minutes is not None:
            total += self.minutes * 60
        if self.hours is not None:
            total += self.hours * 3600
        if self.days is not None:
            total += self.days * 86400
        return total

    def __str__(self) -> str:
        parts = []
        if self.days is not None and self.days > 0:
            parts.append(f"{self.days}d")
        if self.hours is not None and self.hours > 0:
            parts.append(f"{self.hours}h")
        if self.minutes is not None and self.minutes > 0:
            parts.append(f"{self.minutes}m")
        if self.seconds is not None and self.seconds > 0:
            parts.append(f"{self.seconds}s")
        return " ".join(parts) if parts else "0s"


class JobStatus(str, Enum):
    """Status of a scheduled timer job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduledJob(BaseModel):
    """Represents a scheduled timer job."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    duration_seconds: int
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    callback_action: Optional[str] = None
    result: Optional[str] = None


class ScheduleRequest(BaseModel):
    """Request body for scheduling a wait."""

    duration: DurationSchema
    callback_action: str = Field(
        default="timer_expired",
        description="The callback action/name to invoke when the timer expires",
    )
    notify_url: Optional[str] = Field(
        default=None,
        description="Optional URL to receive a notification when the timer completes",
    )


class ScheduleResponse(BaseModel):
    """Response after scheduling a job."""

    job_id: str
    status: str
    duration_seconds: int
    scheduled_at: str
    status_url: str
    message: str


class JobStatusResponse(BaseModel):
    """Response for job status polling."""

    job_id: str
    status: str
    duration_seconds: int
    scheduled_at: str
    completed_at: Optional[str] = None
    callback_action: Optional[str] = None
    result: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    uptime_seconds: Optional[float] = None


class ManifestResponse(BaseModel):
    """MCP manifest describing the service."""

    name: str
    version: str
    description: str
    mcp_version: str
    tools: list[dict] = []
    endpoints: list[str] = []
