"""Tests for scheduler functionality."""

import pytest
import asyncio
from datetime import datetime, timezone

from app.core.scheduler import Scheduler, ScheduledJob, JobStatus, CronParser


class TestCronParser:
    """Tests for cron expression parser."""

    def test_parse_daily_cron(self):
        """Test parsing a daily cron expression."""
        fields = CronParser.parse("0 8 * * *")
        assert fields["minute"] == {0}
        assert fields["hour"] == {8}
        assert len(fields["day"]) == 31
        assert len(fields["month"]) == 12
        assert len(fields["dow"]) == 7

    def test_parse_weekly_cron(self):
        """Test parsing a weekly cron expression."""
        fields = CronParser.parse("0 9 * * 1")
        assert fields["minute"] == {0}
        assert fields["hour"] == {9}
        assert fields["dow"] == {1}

    def test_invalid_cron_raises_error(self):
        """Test that invalid cron raises ValueError."""
        with pytest.raises(ValueError):
            CronParser.parse("invalid")

    def test_get_next_run(self):
        """Test calculating next run time."""
        now = datetime.now(timezone.utc)
        next_run = CronParser.get_next_run("0 8 * * *", after=now)
        assert next_run > now
        assert next_run.minute == 0
        assert next_run.hour == 8


class TestScheduledJob:
    """Tests for ScheduledJob dataclass."""

    def test_job_to_dict(self):
        """Test job serialization."""
        job = ScheduledJob(
            id="test-job",
            name="Test Job",
            cron="0 8 * * *",
            status=JobStatus.PENDING
        )
        data = job.to_dict()
        assert data["id"] == "test-job"
        assert data["name"] == "Test Job"
        assert data["status"] == "pending"


class TestScheduler:
    """Tests for the Scheduler class."""

    @pytest.fixture
    def scheduler(self):
        return Scheduler()

    def test_scheduler_initial_state(self, scheduler):
        """Test initial scheduler state."""
        assert scheduler.is_running is False
        assert len(scheduler.list_jobs()) == 0

    def test_add_cron_job(self, scheduler):
        """Test adding a cron job."""
        job = scheduler.add_cron_job(
            name="Daily Digest",
            cron="0 8 * * *",
            callback=lambda: None,
            job_id="daily_digest"
        )
        assert job.id == "daily_digest"
        assert job.name == "Daily Digest"
        assert job.cron == "0 8 * * *"

    def test_add_interval_job(self, scheduler):
        """Test adding an interval job."""
        job = scheduler.add_interval_job(
            name="Auto Fetch",
            seconds=3600,
            callback=lambda: None,
            job_id="auto_fetch"
        )
        assert job.interval_seconds == 3600
        assert job.id == "auto_fetch"

    def test_get_job(self, scheduler):
        """Test retrieving a job."""
        scheduler.add_cron_job(
            name="Test",
            cron="0 8 * * *",
            callback=lambda: None,
            job_id="test"
        )
        job = scheduler.get_job("test")
        assert job is not None
        assert job.name == "Test"

    def test_get_job_not_found(self, scheduler):
        """Test retrieving non-existent job."""
        job = scheduler.get_job("nonexistent")
        assert job is None

    def test_remove_job(self, scheduler):
        """Test removing a job."""
        scheduler.add_cron_job(
            name="Test",
            cron="0 8 * * *",
            callback=lambda: None,
            job_id="test"
        )
        removed = scheduler.remove_job("test")
        assert removed is True
        assert scheduler.get_job("test") is None

    def test_enable_disable_job(self, scheduler):
        """Test enabling/disabling jobs."""
        job = scheduler.add_cron_job(
            name="Test",
            cron="0 8 * * *",
            callback=lambda: None,
            job_id="test"
        )
        assert job.enabled is True
        
        scheduler.disable_job("test")
        assert scheduler.get_job("test").enabled is False
        
        scheduler.enable_job("test")
        assert scheduler.get_job("test").enabled is True

    def test_is_running_property(self, scheduler):
        """Test the is_running property."""
        assert scheduler.is_running is False
