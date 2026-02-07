"""Tests for the scheduler and cron parser."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.core.scheduler import Scheduler, CronParser, JobStatus, ScheduledJob


class TestCronParser:
    """Tests for CronParser."""
    
    def test_parse_all_wildcards(self):
        """Test parsing '* * * * *' cron expression."""
        fields = CronParser.parse("* * * * *")
        
        assert fields["minute"] == set(range(60))
        assert fields["hour"] == set(range(24))
        assert fields["day"] == set(range(1, 32))
        assert fields["month"] == set(range(1, 13))
        assert fields["dow"] == set(range(7))
    
    def test_parse_specific_values(self):
        """Test parsing specific values."""
        fields = CronParser.parse("30 8 15 6 2")
        
        assert fields["minute"] == {30}
        assert fields["hour"] == {8}
        assert fields["day"] == {15}
        assert fields["month"] == {6}
        assert fields["dow"] == {2}
    
    def test_parse_ranges(self):
        """Test parsing range expressions."""
        fields = CronParser.parse("0-30 9-17 * * 1-5")
        
        assert fields["minute"] == set(range(0, 31))
        assert fields["hour"] == set(range(9, 18))
        assert fields["dow"] == set(range(1, 6))
    
    def test_parse_lists(self):
        """Test parsing comma-separated lists."""
        fields = CronParser.parse("0,15,30,45 * * * *")
        
        assert fields["minute"] == {0, 15, 30, 45}
    
    def test_parse_step_values(self):
        """Test parsing step expressions."""
        fields = CronParser.parse("*/15 * * * *")
        
        assert fields["minute"] == {0, 15, 30, 45}
    
    def test_weekday_sunday_as_zero(self):
        """Test that Sunday is represented as 0 in cron notation."""
        # In cron: 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        fields = CronParser.parse("* * * * 0")
        
        assert fields["dow"] == {0}  # Sunday
    
    def test_get_next_run_specific_minute(self):
        """Test getting next run time for a specific minute."""
        # Run at minute 30 of every hour
        after = datetime(2026, 2, 6, 10, 15, tzinfo=None)  # 10:15 AM
        
        next_run = CronParser.get_next_run("30 * * * *", after=after)
        
        assert next_run.minute == 30
        assert next_run.hour == 10  # Same hour, just minute 30
    
    def test_get_next_run_next_hour(self):
        """Test that next run rolls to next hour when necessary."""
        # Run at minute 15 of every hour
        after = datetime(2026, 2, 6, 10, 30, tzinfo=None)  # 10:30 AM
        
        next_run = CronParser.get_next_run("15 * * * *", after=after)
        
        assert next_run.minute == 15
        assert next_run.hour == 11  # Next hour
    
    def test_get_next_run_weekday_matching(self):
        """Test that weekday matching uses correct cron notation.
        
        Critical bug fix: Python weekday() returns 0=Monday, but cron uses 0=Sunday.
        This test ensures the conversion is correct.
        """
        # February 6, 2026 is a Friday (Python weekday=4, cron weekday=5)
        # We want to run only on Fridays (cron weekday=5)
        after = datetime(2026, 2, 6, 10, 00, tzinfo=None)  # Friday 10:00 AM
        
        # Cron expression: run at minute 30 on Fridays (5 in cron notation)
        next_run = CronParser.get_next_run("30 * * * 5", after=after)
        
        # Should be the same Friday at 10:30
        assert next_run.date() == after.date()
        assert next_run.minute == 30
    
    def test_get_next_run_sunday(self):
        """Test that Sunday (cron day 0) is correctly matched."""
        # February 8, 2026 is a Sunday
        after = datetime(2026, 2, 8, 10, 00, tzinfo=None)  # Sunday
        
        # Run on Sundays (cron weekday=0)
        next_run = CronParser.get_next_run("30 * * * 0", after=after)
        
        # Should find a match on this Sunday
        assert next_run.month == 2
        assert next_run.day == 8  # Same Sunday
        assert next_run.minute == 30


class TestScheduler:
    """Tests for Scheduler."""
    
    @pytest.fixture
    def scheduler(self):
        return Scheduler()
    
    def test_add_cron_job(self, scheduler):
        """Test adding a cron job."""
        callback = AsyncMock()
        
        job = scheduler.add_cron_job(
            name="Test Job",
            cron="0 8 * * *",
            callback=callback
        )
        
        assert job.name == "Test Job"
        assert job.cron == "0 8 * * *"
        assert job.status == JobStatus.PENDING
        assert job.enabled is True
    
    def test_add_interval_job(self, scheduler):
        """Test adding an interval-based job."""
        callback = AsyncMock()
        
        job = scheduler.add_interval_job(
            name="Interval Job",
            seconds=3600,
            callback=callback
        )
        
        assert job.name == "Interval Job"
        assert job.interval_seconds == 3600
        assert job.status == JobStatus.PENDING
    
    def test_remove_job(self, scheduler):
        """Test removing a job."""
        callback = AsyncMock()
        job = scheduler.add_cron_job(
            name="To Remove",
            cron="* * * * *",
            callback=callback
        )
        
        assert job.id in scheduler.jobs
        
        scheduler.remove_job(job.id)
        
        assert job.id not in scheduler.jobs
    
    def test_enable_disable_job(self, scheduler):
        """Test enabling and disabling a job."""
        callback = AsyncMock()
        job = scheduler.add_cron_job(
            name="Toggle Job",
            cron="* * * * *",
            callback=callback
        )
        
        scheduler.disable_job(job.id)
        assert job.enabled is False
        
        scheduler.enable_job(job.id)
        assert job.enabled is True
    
    def test_list_jobs(self, scheduler):
        """Test listing all jobs."""
        callback = AsyncMock()
        
        scheduler.add_cron_job("Job 1", "0 8 * * *", callback)
        scheduler.add_interval_job("Job 2", 3600, callback)
        
        jobs = scheduler.list_jobs()
        
        assert len(jobs) == 2
        names = [j["name"] for j in jobs]
        assert "Job 1" in names
        assert "Job 2" in names


class TestScheduledJob:
    """Tests for ScheduledJob dataclass."""
    
    def test_job_to_dict(self):
        """Test converting job to dictionary."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        job = ScheduledJob(
            id="test-123",
            name="Test Job",
            callback=lambda: None,
            cron="0 8 * * *",
            next_run=now
        )
        
        job_dict = job.to_dict()
        
        assert job_dict["id"] == "test-123"
        assert job_dict["name"] == "Test Job"
        assert job_dict["cron"] == "0 8 * * *"
        assert "next_run" in job_dict
