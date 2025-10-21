# validators.py
"""
Input validation service for the Quran Video Generator API.

This module provides comprehensive validation of all user inputs,
ensuring data integrity and providing clear error messages.
"""
from typing import Optional, Tuple
from pathlib import Path

from exceptions import (
    InvalidSurahError,
    InvalidAyahError,
    InvalidAyahRangeError,
    InvalidReciterError,
    InvalidTranslationError,
    InvalidBackgroundError,
    BackgroundMediaNotFoundError,
    ValidationError
)


class VideoRequestValidator:
    """
    Validator for video generation requests.

    This class encapsulates all validation logic for video generation
    requests, ensuring all parameters are valid before processing.
    """

    def __init__(self, config):
        """
        Initialize the validator with configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.surah_ayah_counts = config.surah_ayah_counts
        self.reciters = config.reciters
        self.translations = config.translations
        self.backgrounds = config.backgrounds

    def validate_surah(self, surah: int) -> None:
        """
        Validate surah number.

        Args:
            surah: Surah number to validate

        Raises:
            InvalidSurahError: If surah is not between 1 and 114
        """
        if not (1 <= surah <= 114):
            raise InvalidSurahError(surah)

    def validate_ayah(self, surah: int, ayah: int) -> None:
        """
        Validate ayah number for the given surah.

        Args:
            surah: Surah number
            ayah: Ayah number to validate

        Raises:
            InvalidSurahError: If surah is invalid
            InvalidAyahError: If ayah is not valid for the given surah
        """
        # First validate surah
        self.validate_surah(surah)

        # Get max ayah for this surah
        max_ayah = self.surah_ayah_counts.get(surah)
        if max_ayah is None:
            # This should never happen if validate_surah passed
            raise InvalidSurahError(surah)

        # Validate ayah is in range
        if not (1 <= ayah <= max_ayah):
            raise InvalidAyahError(surah, ayah, max_ayah)

    def validate_ayah_range(
        self,
        surah: int,
        start_ayah: int,
        end_ayah: int
    ) -> None:
        """
        Validate ayah range for the given surah.

        Args:
            surah: Surah number
            start_ayah: Starting ayah number
            end_ayah: Ending ayah number

        Raises:
            InvalidSurahError: If surah is invalid
            InvalidAyahError: If either ayah is invalid
            InvalidAyahRangeError: If end_ayah < start_ayah
        """
        # Validate both ayahs individually
        self.validate_ayah(surah, start_ayah)
        self.validate_ayah(surah, end_ayah)

        # Validate range
        if end_ayah < start_ayah:
            raise InvalidAyahRangeError(start_ayah, end_ayah)

    def validate_reciter(self, reciter_key: str) -> None:
        """
        Validate reciter key.

        Args:
            reciter_key: Reciter key to validate

        Raises:
            InvalidReciterError: If reciter key is not recognized
        """
        if reciter_key not in self.reciters:
            raise InvalidReciterError(
                reciter_key,
                list(self.reciters.keys())
            )

    def validate_translation(self, translation_key: str) -> None:
        """
        Validate translation key.

        Args:
            translation_key: Translation key to validate

        Raises:
            InvalidTranslationError: If translation key is not recognized
        """
        if translation_key not in self.translations:
            raise InvalidTranslationError(
                translation_key,
                list(self.translations.keys())
            )

    def validate_background(self, background_id: str) -> None:
        """
        Validate background ID and check if file exists.

        Args:
            background_id: Background ID to validate

        Raises:
            InvalidBackgroundError: If background ID is not recognized
            BackgroundMediaNotFoundError: If background file doesn't exist
        """
        if background_id not in self.backgrounds:
            raise InvalidBackgroundError(
                background_id,
                list(self.backgrounds.keys())
            )

        # Check if file exists
        bg_config = self.backgrounds[background_id]
        bg_path = Path(bg_config["path"])
        if not bg_path.is_file():
            raise BackgroundMediaNotFoundError(background_id, str(bg_path))

    def validate_output_filename(self, filename: Optional[str]) -> None:
        """
        Validate output filename.

        Args:
            filename: Optional filename to validate

        Raises:
            ValidationError: If filename contains invalid characters
        """
        if filename is None:
            return

        # Check for invalid characters
        invalid_chars = set('<>:"/\\|?*')
        if any(char in filename for char in invalid_chars):
            raise ValidationError(
                f"Output filename contains invalid characters: {filename}",
                error_code="INVALID_FILENAME",
                details={"filename": filename, "invalid_chars": list(invalid_chars)}
            )

        # Check length
        if len(filename) > 255:
            raise ValidationError(
                f"Output filename too long: {len(filename)} characters (max 255)",
                error_code="FILENAME_TOO_LONG",
                details={"filename": filename, "length": len(filename)}
            )

    def validate_request(
        self,
        surah: int,
        start_ayah: int,
        end_ayah: int,
        reciter_key: str,
        translation_key: str,
        background_id: str,
        output_filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a complete video generation request.

        This is a convenience method that runs all validations and returns
        a summary result.

        Args:
            surah: Surah number
            start_ayah: Starting ayah number
            end_ayah: Ending ayah number
            reciter_key: Reciter identifier
            translation_key: Translation identifier
            background_id: Background media identifier
            output_filename: Optional custom filename

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if all validations pass
            - error_message: None if valid, error message if invalid

        Note:
            This method catches ValidationError exceptions and returns
            them as a tuple. For programmatic use, prefer calling individual
            validation methods and handling exceptions directly.
        """
        try:
            self.validate_ayah_range(surah, start_ayah, end_ayah)
            self.validate_reciter(reciter_key)
            self.validate_translation(translation_key)
            self.validate_background(background_id)
            self.validate_output_filename(output_filename)
            return True, None
        except ValidationError as e:
            return False, e.message

    def get_reciter_info(self, reciter_key: str) -> dict:
        """
        Get reciter information.

        Args:
            reciter_key: Reciter identifier

        Returns:
            Dictionary with reciter information

        Raises:
            InvalidReciterError: If reciter key is invalid
        """
        self.validate_reciter(reciter_key)
        return self.reciters[reciter_key]

    def get_translation_info(self, translation_key: str) -> dict:
        """
        Get translation information.

        Args:
            translation_key: Translation identifier

        Returns:
            Dictionary with translation information

        Raises:
            InvalidTranslationError: If translation key is invalid
        """
        self.validate_translation(translation_key)
        return self.translations[translation_key]

    def get_background_info(self, background_id: str) -> dict:
        """
        Get background information.

        Args:
            background_id: Background identifier

        Returns:
            Dictionary with background information

        Raises:
            InvalidBackgroundError: If background ID is invalid
            BackgroundMediaNotFoundError: If background file doesn't exist
        """
        self.validate_background(background_id)
        return self.backgrounds[background_id]

    def check_reciter_has_timestamps(self, reciter_key: str) -> bool:
        """
        Check if reciter has confirmed word timestamps.

        Args:
            reciter_key: Reciter identifier

        Returns:
            True if reciter has confirmed timestamps, False otherwise

        Raises:
            InvalidReciterError: If reciter key is invalid
        """
        reciter_info = self.get_reciter_info(reciter_key)
        return reciter_info.get("has_timestamps", False)

    def get_max_ayah_for_surah(self, surah: int) -> int:
        """
        Get maximum ayah number for a given surah.

        Args:
            surah: Surah number

        Returns:
            Maximum ayah number for the surah

        Raises:
            InvalidSurahError: If surah is invalid
        """
        self.validate_surah(surah)
        return self.surah_ayah_counts[surah]
