"""Background job scheduler for Timer MCP.

Provides an in-memory scheduler that handles delayed execution of callback actions.
Uses asyncio tasks for non-blocking delayed execution.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from timer_mcp.models import JobStatus, JobStatusResponse, ScheduledJob

logger = logging.getLogger(__name__)

# Module-level job store
_jobs: dict[str, ScheduledJob] = {}
_lock = asyncio.Lock()


async def create_job(
    duration_seconds: int,
    callback_action: str = "timer_expired",
) -> ScheduledJob:
    """Create a new scheduled job and start its timer.

    Args:
        duration_seconds: Duration to wait before executing callback.
        callback_action: Name/description of the callback to execute.

    Returns:
        The created ScheduledJob instance.
    """
    job = ScheduledJob(
        duration_seconds=duration_seconds,
        callback_action=callback_action,
        status=JobStatus.PENDING,
    )
    async with _lock:
        _jobs[job.job_id] = job

    # Schedule the delayed execution
    asyncio.create_task(_run_job(job))
    logger.info("Created job %s: %ds duration, action=%s", job.job_id, duration_seconds, callback_action)
    return job


async def _run_job(job: ScheduledJob) -> None:
    """Execute the delayed job after waiting the specified duration.

    This is the core scheduler logic: waits for the duration, then
    marks the job as completed and sets the result.
    """
    try:
        async with _lock:
            job.status = JobStatus.RUNNING

        logger.info("Job %s: waiting %ds...", job.job_id, job.duration_seconds)

        # Sleep asynchronously for the duration
        await asyncio.sleep(job.duration_seconds)

        # Job completed
        async with _lock:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.result = f"Callback '{job.callback_action}' executed after {job.duration_seconds}s"

        logger.info(
            "Job %s: completed after %ds",
            job.job_id,
            job.duration_seconds,
        )
    except asyncio.CancelledError:
        logger.warning("Job %s: cancelled", job.job_id)
        async with _lock:
            job.status = JobStatus.FAILED
            job.result = "Job was cancelled"
    except Exception as e:
        logger.error("Job %s: failed with error: %s", job.job_id, e)
        async with _lock:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.result = f"Job failed: {str(e)}"


async def get_job_status(job_id: str) -> Optional[JobStatusResponse]:
    """Get the status of a scheduled job.

    Args:
        job_id: The job ID to look up.

    Returns:
        JobStatusResponse if found, None otherwise.
    """
    async with _lock:
        job = _jobs.get(job_id)
    if job is None:
        return None
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        duration_seconds=job.duration_seconds,
        scheduled_at=job.scheduled_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        callback_action=job.callback_action,
        result=job.result,
    )


async def list_jobs() -> list[JobStatusResponse]:
    """List all jobs.

    Returns:
        List of JobStatusResponse for all known jobs.
    """
    async with _lock:
        jobs = list(_jobs.values())
    return [
        JobStatusResponse(
            job_id=j.job_id,
            status=j.status.value,
            duration_seconds=j.duration_seconds,
            scheduled_at=j.scheduled_at.isoformat(),
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
            callback_action=j.callback_action,
            result=j.result,
        )
        for j in jobs
    ]


async def cancel_job(job_id: str) -> bool:
    """Cancel a pending job.

    Args:
        job_id: The job ID to cancel.

    Returns:
        True if the job was found and cancelled, False otherwise.
    """
    async with _lock:
        job = _jobs.get(job_id)

    if job is None:
        return False

    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        return False

    async with _lock:
        job.status = JobStatus.FAILED
        job.result = "Job was cancelled by user"

    logger.info("Job %s: cancelled by user", job_id)
    return True


async def clear_completed() -> int:
    """Remove all completed/failed jobs from memory.

    Returns:
        Number of jobs removed.
    """
    async with _lock:
        to_remove = [
            jid for jid, j in _jobs.items()
            if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]
        for jid in to_remove:
            del _jobs[jid]
    return len(to_remove)
