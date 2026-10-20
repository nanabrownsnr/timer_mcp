"""Tests for the background scheduler module."""

import asyncio

import pytest

from timer_mcp.models import JobStatus
from timer_mcp.scheduler import (
    _jobs,
    create_job,
    get_job_status,
    list_jobs,
    cancel_job,
    clear_completed,
)


@pytest.fixture(autouse=True)
def clear_jobs():
    """Clear all jobs before each test."""
    _jobs.clear()
    yield
    _jobs.clear()


class TestCreateJob:
    """Tests for job creation."""

    @pytest.mark.asyncio
    async def test_create_job_basic(self):
        job = await create_job(duration_seconds=5, callback_action="test_callback")
        assert job.job_id is not None
        assert job.duration_seconds == 5
        assert job.callback_action == "test_callback"
        assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_job_default_callback(self):
        job = await create_job(duration_seconds=1)
        assert job.callback_action == "timer_expired"

    @pytest.mark.asyncio
    async def test_create_job_zero_duration(self):
        job = await create_job(duration_seconds=0)
        assert job.duration_seconds == 0

    @pytest.mark.asyncio
    async def test_job_has_uuid(self):
        job = await create_job(duration_seconds=1)
        assert len(job.job_id) == 36


class TestJobStatus:
    """Tests for job status tracking."""

    @pytest.mark.asyncio
    async def test_get_job_status_pending(self):
        job = await create_job(duration_seconds=60)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert status.status == JobStatus.PENDING.value
        assert status.duration_seconds == 60
        assert status.job_id == job.job_id

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        status = await get_job_status("nonexistent-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_job_status_completed(self):
        job = await create_job(duration_seconds=1, callback_action="quick_test")
        await asyncio.sleep(1.5)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert status.status == JobStatus.COMPLETED.value
        assert status.result is not None
        assert "quick_test" in status.result

    @pytest.mark.asyncio
    async def test_job_has_scheduled_timestamp(self):
        job = await create_job(duration_seconds=10)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert "scheduled_at" in status.model_dump()


class TestListJobs:
    """Tests for listing jobs."""

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self):
        jobs = await list_jobs()
        assert jobs == []

    @pytest.mark.asyncio
    async def test_list_jobs_multiple(self):
        job1 = await create_job(duration_seconds=10, callback_action="action1")
        job2 = await create_job(duration_seconds=20, callback_action="action2")
        jobs = await list_jobs()
        assert len(jobs) == 2
        job_ids = {j.job_id for j in jobs}
        assert job1.job_id in job_ids
        assert job2.job_id in job_ids


class TestCancelJob:
    """Tests for job cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self):
        job = await create_job(duration_seconds=60)
        result = await cancel_job(job.job_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self):
        result = await cancel_job("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self):
        job = await create_job(duration_seconds=1)
        await asyncio.sleep(1.5)
        result = await cancel_job(job.job_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_job_sets_status(self):
        job = await create_job(duration_seconds=60)
        await cancel_job(job.job_id)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert status.status == JobStatus.FAILED.value


class TestClearCompleted:
    """Tests for clearing completed jobs."""

    @pytest.mark.asyncio
    async def test_clear_no_completed_jobs(self):
        count = await clear_completed()
        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_completed_jobs(self):
        job = await create_job(duration_seconds=1)
        await asyncio.sleep(1.5)
        count = await clear_completed()
        assert count == 1
        jobs = await list_jobs()
        assert len(jobs) == 0


class TestJobExecution:
    """Tests for actual job execution."""

    @pytest.mark.asyncio
    async def test_job_completes_after_duration(self):
        job = await create_job(duration_seconds=2, callback_action="test_exec")
        await asyncio.sleep(2.5)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert status.status == JobStatus.COMPLETED.value
        assert status.result is not None

    @pytest.mark.asyncio
    async def test_job_short_duration(self):
        job = await create_job(duration_seconds=1)
        await asyncio.sleep(1.5)
        status = await get_job_status(job.job_id)
        assert status is not None
        assert status.status == JobStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_multiple_jobs_execute_independently(self):
        job1 = await create_job(duration_seconds=1, callback_action="fast")
        job2 = await create_job(duration_seconds=2, callback_action="slow")

        await asyncio.sleep(1.5)
        status1 = await get_job_status(job1.job_id)
        assert status1 is not None
        assert status1.status == JobStatus.COMPLETED.value

        await asyncio.sleep(1.0)
        status2 = await get_job_status(job2.job_id)
        assert status2 is not None
        assert status2.status == JobStatus.COMPLETED.value
