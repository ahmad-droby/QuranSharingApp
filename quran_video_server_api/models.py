# models.py
"""
Database models for the Quran Video Generator API.

This module defines SQLAlchemy ORM models for persisting job data,
ensuring state is maintained across server restarts.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Enum as SQLEnum,
    create_engine, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Enumeration of possible job statuses."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoJob(Base):
    """
    Represents a video generation job with full state tracking.

    Attributes:
        job_id: Unique identifier for the job (UUID)
        status: Current job status (queued, processing, completed, failed, cancelled)
        surah: Surah number (1-114)
        start_ayah: Starting ayah number
        end_ayah: Ending ayah number (inclusive)
        reciter_key: Key identifying the reciter
        translation_key: Key identifying the translation
        background_id: Key identifying the background media
        output_filename: Custom output filename (optional)
        output_path: Path to the generated video file (when completed)
        detail: Current processing detail or error message
        progress_percentage: Progress indicator (0-100)
        created_at: Timestamp when job was created
        started_at: Timestamp when processing began
        completed_at: Timestamp when processing finished (success or failure)
        error_message: Detailed error information if job failed
    """
    __tablename__ = "video_jobs"

    # Primary key
    job_id = Column(String(36), primary_key=True, index=True)

    # Job status
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.QUEUED, index=True)

    # Request parameters
    surah = Column(Integer, nullable=False)
    start_ayah = Column(Integer, nullable=False)
    end_ayah = Column(Integer, nullable=False)
    reciter_key = Column(String(50), nullable=False)
    translation_key = Column(String(50), nullable=False)
    background_id = Column(String(50), nullable=False)
    output_filename = Column(String(255), nullable=True)

    # Result data
    output_path = Column(String(512), nullable=True)
    detail = Column(Text, nullable=True)
    progress_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VideoJob(job_id={self.job_id}, status={self.status.value}, "
            f"surah={self.surah}, ayahs={self.start_ayah}-{self.end_ayah})>"
        )

    def to_dict(self) -> dict:
        """Convert the job to a dictionary representation."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "surah": self.surah,
            "start_ayah": self.start_ayah,
            "end_ayah": self.end_ayah,
            "reciter_key": self.reciter_key,
            "translation_key": self.translation_key,
            "background_id": self.background_id,
            "output_filename": self.output_filename,
            "output_path": self.output_path,
            "detail": self.detail,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


# Database setup functions
def get_database_url(db_path: str = "quran_video_jobs.db") -> str:
    """
    Construct the database URL.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        SQLAlchemy database URL string
    """
    return f"sqlite:///{db_path}"


def create_database_engine(database_url: str, echo: bool = False):
    """
    Create a SQLAlchemy engine.

    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements (for debugging)

    Returns:
        SQLAlchemy Engine instance
    """
    return create_engine(
        database_url,
        echo=echo,
        connect_args={"check_same_thread": False}  # Needed for SQLite with FastAPI
    )


def create_session_maker(engine):
    """
    Create a session maker bound to the given engine.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        Session maker factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database(engine):
    """
    Initialize the database by creating all tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)
