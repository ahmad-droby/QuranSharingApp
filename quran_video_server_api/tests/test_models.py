# tests/test_models.py
"""Tests for database models."""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from models import (
    VideoJob, JobStatus, get_database_url, create_database_engine,
    create_session_maker, init_database, Base
)


@pytest.fixture
def test_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def engine(test_db_path):
    """Create a test database engine."""
    db_url = get_database_url(str(test_db_path))
    test_engine = create_database_engine(db_url, echo=False)
    init_database(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_maker(engine):
    """Create a session maker for testing."""
    return create_session_maker(engine)


@pytest.fixture
def session(session_maker):
    """Create a database session for testing."""
    test_session = session_maker()
    yield test_session
    test_session.close()


class TestVideoJob:
    """Tests for VideoJob model."""

    def test_create_video_job(self, session):
        """Test creating a new video job."""
        job = VideoJob(
            job_id="test-job-123",
            status=JobStatus.QUEUED,
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        session.add(job)
        session.commit()

        # Retrieve the job
        retrieved_job = session.query(VideoJob).filter_by(job_id="test-job-123").first()

        assert retrieved_job is not None
        assert retrieved_job.job_id == "test-job-123"
        assert retrieved_job.status == JobStatus.QUEUED
        assert retrieved_job.surah == 1
        assert retrieved_job.start_ayah == 1
        assert retrieved_job.end_ayah == 7
        assert retrieved_job.reciter_key == "mishary_alafasy"
        assert retrieved_job.translation_key == "en_sahih"
        assert retrieved_job.background_id == "nature_video"
        assert retrieved_job.progress_percentage == 0.0
        assert retrieved_job.created_at is not None

    def test_video_job_repr(self, session):
        """Test VideoJob string representation."""
        job = VideoJob(
            job_id="test-job-456",
            status=JobStatus.PROCESSING,
            surah=2,
            start_ayah=1,
            end_ayah=5,
            reciter_key="sudais",
            translation_key="en_yusufali",
            background_id="calm_image"
        )

        session.add(job)
        session.commit()

        job_repr = repr(job)
        assert "test-job-456" in job_repr
        assert "processing" in job_repr
        assert "surah=2" in job_repr
        assert "ayahs=1-5" in job_repr

    def test_video_job_to_dict(self, session):
        """Test converting VideoJob to dictionary."""
        job = VideoJob(
            job_id="test-job-789",
            status=JobStatus.COMPLETED,
            surah=3,
            start_ayah=1,
            end_ayah=10,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video",
            output_path="/path/to/output.mp4",
            progress_percentage=100.0
        )

        session.add(job)
        session.commit()

        job_dict = job.to_dict()

        assert job_dict["job_id"] == "test-job-789"
        assert job_dict["status"] == "completed"
        assert job_dict["surah"] == 3
        assert job_dict["start_ayah"] == 1
        assert job_dict["end_ayah"] == 10
        assert job_dict["reciter_key"] == "mishary_alafasy"
        assert job_dict["translation_key"] == "en_sahih"
        assert job_dict["background_id"] == "nature_video"
        assert job_dict["output_path"] == "/path/to/output.mp4"
        assert job_dict["progress_percentage"] == 100.0
        assert "created_at" in job_dict

    def test_video_job_timestamps(self, session):
        """Test VideoJob timestamp management."""
        job = VideoJob(
            job_id="test-job-timestamps",
            status=JobStatus.QUEUED,
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        session.add(job)
        session.commit()

        # Check initial timestamps
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None

        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        session.commit()

        assert job.started_at is not None
        assert job.completed_at is None

        # Update status to completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        session.commit()

        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.completed_at >= job.started_at
        assert job.started_at >= job.created_at

    def test_video_job_with_error(self, session):
        """Test VideoJob with error information."""
        job = VideoJob(
            job_id="test-job-error",
            status=JobStatus.FAILED,
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video",
            error_message="API connection timeout",
            detail="Failed to fetch data from Quran.com API"
        )

        session.add(job)
        session.commit()

        retrieved_job = session.query(VideoJob).filter_by(job_id="test-job-error").first()

        assert retrieved_job.status == JobStatus.FAILED
        assert retrieved_job.error_message == "API connection timeout"
        assert retrieved_job.detail == "Failed to fetch data from Quran.com API"

    def test_job_status_enum(self):
        """Test JobStatus enumeration."""
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_database_initialization(self, engine):
        """Test that database tables are created correctly."""
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "video_jobs" in tables

        # Check columns
        columns = {col["name"] for col in inspector.get_columns("video_jobs")}
        expected_columns = {
            "job_id", "status", "surah", "start_ayah", "end_ayah",
            "reciter_key", "translation_key", "background_id",
            "output_filename", "output_path", "detail", "progress_percentage",
            "created_at", "started_at", "completed_at", "error_message"
        }

        assert expected_columns.issubset(columns)
