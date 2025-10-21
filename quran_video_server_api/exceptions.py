# exceptions.py
"""
Custom exception hierarchy for the Quran Video Generator API.

This module defines a structured exception hierarchy that provides clear,
actionable error information throughout the application.
"""
from typing import Optional, Dict, Any


class QuranVideoError(Exception):
    """Base exception for all Quran Video Generator errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# API-related exceptions
class APIError(QuranVideoError):
    """Base class for external API errors."""
    pass


class QuranAPIError(APIError):
    """Error communicating with Quran.com API."""

    def __init__(self, message: str, surah: Optional[int] = None, ayah: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="QURAN_API_ERROR",
            details={"surah": surah, "ayah": ayah}
        )


class TranslationAPIError(APIError):
    """Error communicating with translation API."""

    def __init__(self, message: str, surah: Optional[int] = None, ayah: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="TRANSLATION_API_ERROR",
            details={"surah": surah, "ayah": ayah}
        )


class APITimeoutError(APIError):
    """API request timed out."""

    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="API_TIMEOUT_ERROR",
            details={"url": url}
        )


class APIRateLimitError(APIError):
    """API rate limit exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="API_RATE_LIMIT_ERROR",
            details={"retry_after": retry_after}
        )


# Validation exceptions
class ValidationError(QuranVideoError):
    """Base class for validation errors."""
    pass


class InvalidSurahError(ValidationError):
    """Invalid surah number."""

    def __init__(self, surah: int):
        super().__init__(
            message=f"Invalid surah number: {surah}. Must be between 1 and 114.",
            error_code="INVALID_SURAH",
            details={"surah": surah}
        )


class InvalidAyahError(ValidationError):
    """Invalid ayah number for the given surah."""

    def __init__(self, surah: int, ayah: int, max_ayah: int):
        super().__init__(
            message=f"Invalid ayah number: {ayah} for surah {surah}. Must be between 1 and {max_ayah}.",
            error_code="INVALID_AYAH",
            details={"surah": surah, "ayah": ayah, "max_ayah": max_ayah}
        )


class InvalidAyahRangeError(ValidationError):
    """Invalid ayah range."""

    def __init__(self, start_ayah: int, end_ayah: int):
        super().__init__(
            message=f"Invalid ayah range: {start_ayah}-{end_ayah}. End ayah must be >= start ayah.",
            error_code="INVALID_AYAH_RANGE",
            details={"start_ayah": start_ayah, "end_ayah": end_ayah}
        )


class InvalidReciterError(ValidationError):
    """Invalid reciter key."""

    def __init__(self, reciter_key: str, valid_keys: list):
        super().__init__(
            message=f"Invalid reciter key: '{reciter_key}'. Valid keys: {', '.join(valid_keys)}",
            error_code="INVALID_RECITER",
            details={"reciter_key": reciter_key, "valid_keys": valid_keys}
        )


class InvalidTranslationError(ValidationError):
    """Invalid translation key."""

    def __init__(self, translation_key: str, valid_keys: list):
        super().__init__(
            message=f"Invalid translation key: '{translation_key}'. Valid keys: {', '.join(valid_keys)}",
            error_code="INVALID_TRANSLATION",
            details={"translation_key": translation_key, "valid_keys": valid_keys}
        )


class InvalidBackgroundError(ValidationError):
    """Invalid background ID."""

    def __init__(self, background_id: str, valid_ids: list):
        super().__init__(
            message=f"Invalid background ID: '{background_id}'. Valid IDs: {', '.join(valid_ids)}",
            error_code="INVALID_BACKGROUND",
            details={"background_id": background_id, "valid_ids": valid_ids}
        )


# Resource exceptions
class ResourceError(QuranVideoError):
    """Base class for resource-related errors."""
    pass


class AudioDownloadError(ResourceError):
    """Failed to download audio file."""

    def __init__(self, url: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Failed to download audio from {url}: {reason or 'Unknown error'}",
            error_code="AUDIO_DOWNLOAD_ERROR",
            details={"url": url, "reason": reason}
        )


class AudioProcessingError(ResourceError):
    """Failed to process audio file."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUDIO_PROCESSING_ERROR",
            details={"file_path": file_path}
        )


class VideoGenerationError(ResourceError):
    """Failed to generate video."""

    def __init__(self, message: str, job_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VIDEO_GENERATION_ERROR",
            details={"job_id": job_id}
        )


class BackgroundMediaNotFoundError(ResourceError):
    """Background media file not found."""

    def __init__(self, background_id: str, file_path: str):
        super().__init__(
            message=f"Background media file not found: {file_path}",
            error_code="BACKGROUND_NOT_FOUND",
            details={"background_id": background_id, "file_path": file_path}
        )


class InsufficientDiskSpaceError(ResourceError):
    """Insufficient disk space for operation."""

    def __init__(self, required_mb: int, available_mb: int):
        super().__init__(
            message=f"Insufficient disk space. Required: {required_mb}MB, Available: {available_mb}MB",
            error_code="INSUFFICIENT_DISK_SPACE",
            details={"required_mb": required_mb, "available_mb": available_mb}
        )


# Job exceptions
class JobError(QuranVideoError):
    """Base class for job-related errors."""
    pass


class JobNotFoundError(JobError):
    """Job ID not found in database."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job not found: {job_id}",
            error_code="JOB_NOT_FOUND",
            details={"job_id": job_id}
        )


class JobAlreadyExistsError(JobError):
    """Job ID already exists in database."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job already exists: {job_id}",
            error_code="JOB_ALREADY_EXISTS",
            details={"job_id": job_id}
        )


class JobCancelledException(JobError):
    """Job was cancelled."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job was cancelled: {job_id}",
            error_code="JOB_CANCELLED",
            details={"job_id": job_id}
        )


class MaxConcurrentJobsError(JobError):
    """Maximum concurrent jobs limit reached."""

    def __init__(self, max_jobs: int):
        super().__init__(
            message=f"Maximum concurrent jobs limit reached: {max_jobs}",
            error_code="MAX_CONCURRENT_JOBS",
            details={"max_jobs": max_jobs}
        )


# Data exceptions
class DataError(QuranVideoError):
    """Base class for data-related errors."""
    pass


class MissingTimestampError(DataError):
    """Word timestamps missing from API response."""

    def __init__(self, surah: int, ayah: int, reciter: str):
        super().__init__(
            message=f"No word timestamps available for surah {surah}, ayah {ayah} with reciter {reciter}",
            error_code="MISSING_TIMESTAMPS",
            details={"surah": surah, "ayah": ayah, "reciter": reciter}
        )


class MissingArabicTextError(DataError):
    """Arabic text missing from API response."""

    def __init__(self, surah: int, ayah: int):
        super().__init__(
            message=f"Arabic text missing for surah {surah}, ayah {ayah}",
            error_code="MISSING_ARABIC_TEXT",
            details={"surah": surah, "ayah": ayah}
        )


class MissingTranslationError(DataError):
    """Translation text missing from API response."""

    def __init__(self, surah: int, ayah: int, translation_key: str):
        super().__init__(
            message=f"Translation missing for surah {surah}, ayah {ayah} with key {translation_key}",
            error_code="MISSING_TRANSLATION",
            details={"surah": surah, "ayah": ayah, "translation_key": translation_key}
        )


# Configuration exceptions
class ConfigurationError(QuranVideoError):
    """Base class for configuration errors."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing."""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"Required configuration missing: {config_key}",
            error_code="MISSING_CONFIGURATION",
            details={"config_key": config_key}
        )


class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration value."""

    def __init__(self, config_key: str, value: Any, reason: str):
        super().__init__(
            message=f"Invalid configuration for {config_key}: {reason}",
            error_code="INVALID_CONFIGURATION",
            details={"config_key": config_key, "value": str(value), "reason": reason}
        )
