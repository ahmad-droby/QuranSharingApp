# tests/test_repository.py
"""Tests for the job repository."""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from models import (
    VideoJob, JobStatus, create_database_engine,
    create_session_maker, init_database
)
from repository import JobRepository


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    db_url = f"sqlite:///{db_path}"
    engine = create_database_engine(db_url, echo=False)
    init_database(engine)
    session_maker = create_session_maker(engine)

    yield session_maker

    # Cleanup
    engine.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def repo(test_db):
    """Create a test repository instance."""
    return JobRepository(test_db)


class TestJobRepository:
    """Tests for JobRepository."""

    def test_create_job(self, repo):
        """Test creating a new job."""
        job = repo.create_job(
            job_id="test-create-123",
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        assert job is not None
        assert job.job_id == "test-create-123"
        assert job.status == JobStatus.QUEUED
        assert job.surah == 1
        assert job.start_ayah == 1
        assert job.end_ayah == 7
        assert job.created_at is not None

    def test_get_job(self, repo):
        """Test retrieving a job by ID."""
        # Create a job
        created_job = repo.create_job(
            job_id="test-get-456",
            surah=2,
            start_ayah=1,
            end_ayah=10,
            reciter_key="sudais",
            translation_key="en_yusufali",
            background_id="calm_image"
        )

        # Retrieve the job
        retrieved_job = repo.get_job("test-get-456")

        assert retrieved_job is not None
        assert retrieved_job.job_id == created_job.job_id
        assert retrieved_job.surah == 2
        assert retrieved_job.start_ayah == 1
        assert retrieved_job.end_ayah == 10

    def test_get_nonexistent_job(self, repo):
        """Test retrieving a job that doesn't exist."""
        job = repo.get_job("nonexistent-job-id")
        assert job is None

    def test_update_status(self, repo):
        """Test updating job status."""
        # Create a job
        repo.create_job(
            job_id="test-update-789",
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        # Update status
        success = repo.update_status(
            job_id="test-update-789",
            status=JobStatus.PROCESSING,
            detail="Fetching data...",
            progress_percentage=25.0
        )

        assert success is True

        # Verify update
        job = repo.get_job("test-update-789")
        assert job.status == JobStatus.PROCESSING
        assert job.detail == "Fetching data..."
        assert job.progress_percentage == 25.0
        assert job.started_at is not None

    def test_update_nonexistent_job_status(self, repo):
        """Test updating status of nonexistent job."""
        success = repo.update_status(
            job_id="nonexistent-job",
            status=JobStatus.PROCESSING
        )

        assert success is False

    def test_mark_completed(self, repo):
        """Test marking a job as completed."""
        # Create a job
        repo.create_job(
            job_id="test-complete-abc",
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        # Mark as completed
        success = repo.mark_completed(
            job_id="test-complete-abc",
            output_path="/path/to/output.mp4",
            detail="Video generated successfully"
        )

        assert success is True

        # Verify
        job = repo.get_job("test-complete-abc")
        assert job.status == JobStatus.COMPLETED
        assert job.output_path == "/path/to/output.mp4"
        assert job.progress_percentage == 100.0
        assert job.detail == "Video generated successfully"
        assert job.completed_at is not None

    def test_mark_failed(self, repo):
        """Test marking a job as failed."""
        # Create a job
        repo.create_job(
            job_id="test-failed-def",
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        # Mark as failed
        success = repo.mark_failed(
            job_id="test-failed-def",
            error_message="API connection timeout",
            detail="Failed to fetch data from Quran.com API"
        )

        assert success is True

        # Verify
        job = repo.get_job("test-failed-def")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "API connection timeout"
        assert job.detail == "Failed to fetch data from Quran.com API"
        assert job.completed_at is not None

    def test_get_jobs_by_status(self, repo):
        """Test retrieving jobs filtered by status."""
        # Create multiple jobs with different statuses
        repo.create_job(
            job_id="queued-1", surah=1, start_ayah=1, end_ayah=7,
            reciter_key="mishary_alafasy", translation_key="en_sahih",
            background_id="nature_video"
        )
        repo.create_job(
            job_id="queued-2", surah=2, start_ayah=1, end_ayah=5,
            reciter_key="sudais", translation_key="en_yusufali",
            background_id="calm_image"
        )

        # Update one to processing
        repo.update_status("queued-1", JobStatus.PROCESSING)

        # Query by status
        queued_jobs = repo.get_jobs_by_status(JobStatus.QUEUED)
        processing_jobs = repo.get_jobs_by_status(JobStatus.PROCESSING)

        assert len(queued_jobs) == 1
        assert queued_jobs[0].job_id == "queued-2"

        assert len(processing_jobs) == 1
        assert processing_jobs[0].job_id == "queued-1"

    def test_get_recent_jobs(self, repo):
        """Test retrieving recent jobs."""
        # Create multiple jobs
        for i in range(5):
            repo.create_job(
                job_id=f"recent-job-{i}",
                surah=1, start_ayah=1, end_ayah=7,
                reciter_key="mishary_alafasy",
                translation_key="en_sahih",
                background_id="nature_video"
            )

        # Get recent jobs
        recent_jobs = repo.get_recent_jobs(limit=3)

        assert len(recent_jobs) == 3
        # Should be ordered by created_at desc, so most recent first
        assert recent_jobs[0].job_id == "recent-job-4"
        assert recent_jobs[1].job_id == "recent-job-3"
        assert recent_jobs[2].job_id == "recent-job-2"

    def test_delete_job(self, repo):
        """Test deleting a job."""
        # Create a job
        repo.create_job(
            job_id="test-delete-ghi",
            surah=1, start_ayah=1, end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        # Verify it exists
        job = repo.get_job("test-delete-ghi")
        assert job is not None

        # Delete it
        success = repo.delete_job("test-delete-ghi")
        assert success is True

        # Verify it's gone
        job = repo.get_job("test-delete-ghi")
        assert job is None

    def test_delete_nonexistent_job(self, repo):
        """Test deleting a job that doesn't exist."""
        success = repo.delete_job("nonexistent-job")
        assert success is False

    def test_get_job_count_by_status(self, repo):
        """Test getting job count grouped by status."""
        # Create jobs with different statuses
        repo.create_job(
            job_id="count-queued-1", surah=1, start_ayah=1, end_ayah=7,
            reciter_key="mishary_alafasy", translation_key="en_sahih",
            background_id="nature_video"
        )
        repo.create_job(
            job_id="count-queued-2", surah=1, start_ayah=1, end_ayah=7,
            reciter_key="mishary_alafasy", translation_key="en_sahih",
            background_id="nature_video"
        )
        repo.update_status("count-queued-1", JobStatus.PROCESSING)
        repo.mark_completed("count-queued-2", "/path/to/output.mp4")

        # Get counts
        counts = repo.get_job_count_by_status()

        assert counts.get("queued", 0) == 0  # None left queued
        assert counts.get("processing", 0) == 1
        assert counts.get("completed", 0) == 1
