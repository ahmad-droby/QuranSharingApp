# repository.py
"""
Repository layer for database operations.

This module provides a clean interface for interacting with the database,
abstracting away SQLAlchemy details from the rest of the application.
"""
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy.orm import Session

from models import VideoJob, JobStatus


class JobRepository:
    """
    Repository for managing VideoJob entities in the database.

    This class encapsulates all database operations related to video jobs,
    providing a clean API for CRUD operations and queries.
    """

    def __init__(self, session_maker):
        """
        Initialize the repository with a session maker.

        Args:
            session_maker: SQLAlchemy session maker factory
        """
        self.session_maker = session_maker

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy Session instance

        Example:
            with repo.get_session() as session:
                job = session.query(VideoJob).first()
        """
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_job(
        self,
        job_id: str,
        surah: int,
        start_ayah: int,
        end_ayah: int,
        reciter_key: str,
        translation_key: str,
        background_id: str,
        output_filename: Optional[str] = None
    ) -> VideoJob:
        """
        Create a new video generation job.

        Args:
            job_id: Unique identifier for the job
            surah: Surah number
            start_ayah: Starting ayah number
            end_ayah: Ending ayah number
            reciter_key: Reciter identifier
            translation_key: Translation identifier
            background_id: Background media identifier
            output_filename: Optional custom filename

        Returns:
            Created VideoJob instance
        """
        session = self.session_maker()
        try:
            job = VideoJob(
                job_id=job_id,
                status=JobStatus.QUEUED,
                surah=surah,
                start_ayah=start_ayah,
                end_ayah=end_ayah,
                reciter_key=reciter_key,
                translation_key=translation_key,
                background_id=background_id,
                output_filename=output_filename,
                created_at=datetime.utcnow()
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            # Make object detached but with all attributes loaded
            session.expunge(job)
            return job
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        """
        Retrieve a job by its ID.

        Args:
            job_id: The job identifier

        Returns:
            VideoJob instance if found, None otherwise
        """
        with self.get_session() as session:
            job = session.query(VideoJob).filter(VideoJob.job_id == job_id).first()
            if job:
                # Detach from session to avoid lazy loading issues
                session.expunge(job)
            return job

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        detail: Optional[str] = None,
        progress_percentage: Optional[float] = None
    ) -> bool:
        """
        Update the status of a job.

        Args:
            job_id: The job identifier
            status: New status
            detail: Optional detail message
            progress_percentage: Optional progress value (0-100)

        Returns:
            True if job was updated, False if job not found
        """
        with self.get_session() as session:
            job = session.query(VideoJob).filter(VideoJob.job_id == job_id).first()
            if not job:
                return False

            job.status = status
            if detail is not None:
                job.detail = detail
            if progress_percentage is not None:
                job.progress_percentage = progress_percentage

            # Update timestamps based on status
            if status == JobStatus.PROCESSING and job.started_at is None:
                job.started_at = datetime.utcnow()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                if job.completed_at is None:
                    job.completed_at = datetime.utcnow()

            session.commit()
            return True

    def mark_completed(
        self,
        job_id: str,
        output_path: str,
        detail: Optional[str] = None
    ) -> bool:
        """
        Mark a job as completed successfully.

        Args:
            job_id: The job identifier
            output_path: Path to the generated video file
            detail: Optional completion message

        Returns:
            True if job was updated, False if job not found
        """
        with self.get_session() as session:
            job = session.query(VideoJob).filter(VideoJob.job_id == job_id).first()
            if not job:
                return False

            job.status = JobStatus.COMPLETED
            job.output_path = output_path
            job.progress_percentage = 100.0
            if detail:
                job.detail = detail
            if job.completed_at is None:
                job.completed_at = datetime.utcnow()

            session.commit()
            return True

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
        detail: Optional[str] = None
    ) -> bool:
        """
        Mark a job as failed.

        Args:
            job_id: The job identifier
            error_message: Error description
            detail: Optional additional error detail

        Returns:
            True if job was updated, False if job not found
        """
        with self.get_session() as session:
            job = session.query(VideoJob).filter(VideoJob.job_id == job_id).first()
            if not job:
                return False

            job.status = JobStatus.FAILED
            job.error_message = error_message
            if detail:
                job.detail = detail
            if job.completed_at is None:
                job.completed_at = datetime.utcnow()

            session.commit()
            return True

    def get_jobs_by_status(self, status: JobStatus, limit: int = 100) -> List[VideoJob]:
        """
        Retrieve jobs by status.

        Args:
            status: The status to filter by
            limit: Maximum number of jobs to return

        Returns:
            List of VideoJob instances
        """
        with self.get_session() as session:
            jobs = (
                session.query(VideoJob)
                .filter(VideoJob.status == status)
                .order_by(VideoJob.created_at.desc())
                .limit(limit)
                .all()
            )
            # Detach from session
            for job in jobs:
                session.expunge(job)
            return jobs

    def get_recent_jobs(self, limit: int = 100) -> List[VideoJob]:
        """
        Retrieve the most recent jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of VideoJob instances ordered by creation time (newest first)
        """
        with self.get_session() as session:
            jobs = (
                session.query(VideoJob)
                .order_by(VideoJob.created_at.desc())
                .limit(limit)
                .all()
            )
            # Detach from session
            for job in jobs:
                session.expunge(job)
            return jobs

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the database.

        Args:
            job_id: The job identifier

        Returns:
            True if job was deleted, False if job not found
        """
        with self.get_session() as session:
            job = session.query(VideoJob).filter(VideoJob.job_id == job_id).first()
            if not job:
                return False
            session.delete(job)
            session.commit()
            return True

    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """
        Delete jobs older than the specified number of days.

        Args:
            days_old: Age threshold in days

        Returns:
            Number of jobs deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        with self.get_session() as session:
            deleted_count = (
                session.query(VideoJob)
                .filter(VideoJob.created_at < cutoff_date)
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count

    def get_job_count_by_status(self) -> dict:
        """
        Get count of jobs grouped by status.

        Returns:
            Dictionary mapping status to count
        """
        from sqlalchemy import func

        with self.get_session() as session:
            results = (
                session.query(VideoJob.status, func.count(VideoJob.job_id))
                .group_by(VideoJob.status)
                .all()
            )
            return {status.value: count for status, count in results}
