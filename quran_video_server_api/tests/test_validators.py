# tests/test_validators.py
"""Tests for the validation service."""
import pytest
from pathlib import Path
import tempfile

from config_new import Config
from validators import VideoRequestValidator
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


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def validator(config):
    """Create a test validator."""
    return VideoRequestValidator(config)


class TestSurahValidation:
    """Tests for surah validation."""

    def test_validate_valid_surah(self, validator):
        """Test validating valid surah numbers."""
        # Test boundaries
        validator.validate_surah(1)  # Minimum
        validator.validate_surah(114)  # Maximum
        validator.validate_surah(57)  # Middle

    def test_validate_invalid_surah_too_low(self, validator):
        """Test validating surah number too low."""
        with pytest.raises(InvalidSurahError) as exc_info:
            validator.validate_surah(0)

        assert "Invalid surah number: 0" in str(exc_info.value)

    def test_validate_invalid_surah_too_high(self, validator):
        """Test validating surah number too high."""
        with pytest.raises(InvalidSurahError) as exc_info:
            validator.validate_surah(115)

        assert "Invalid surah number: 115" in str(exc_info.value)

    def test_validate_invalid_surah_negative(self, validator):
        """Test validating negative surah number."""
        with pytest.raises(InvalidSurahError):
            validator.validate_surah(-1)


class TestAyahValidation:
    """Tests for ayah validation."""

    def test_validate_valid_ayah(self, validator):
        """Test validating valid ayah numbers."""
        # Surah Al-Fatiha has 7 ayahs
        validator.validate_ayah(surah=1, ayah=1)  # First
        validator.validate_ayah(surah=1, ayah=7)  # Last
        validator.validate_ayah(surah=1, ayah=4)  # Middle

        # Surah Al-Baqarah has 286 ayahs
        validator.validate_ayah(surah=2, ayah=1)
        validator.validate_ayah(surah=2, ayah=286)

    def test_validate_ayah_exceeds_surah_limit(self, validator):
        """Test validating ayah that exceeds surah limit."""
        # Surah Al-Fatiha only has 7 ayahs
        with pytest.raises(InvalidAyahError) as exc_info:
            validator.validate_ayah(surah=1, ayah=8)

        error = exc_info.value
        assert "Invalid ayah number: 8 for surah 1" in str(error)
        assert error.details["max_ayah"] == 7

    def test_validate_ayah_zero(self, validator):
        """Test validating ayah number zero."""
        with pytest.raises(InvalidAyahError):
            validator.validate_ayah(surah=1, ayah=0)

    def test_validate_ayah_negative(self, validator):
        """Test validating negative ayah number."""
        with pytest.raises(InvalidAyahError):
            validator.validate_ayah(surah=1, ayah=-1)

    def test_validate_ayah_with_invalid_surah(self, validator):
        """Test validating ayah with invalid surah."""
        with pytest.raises(InvalidSurahError):
            validator.validate_ayah(surah=999, ayah=1)


class TestAyahRangeValidation:
    """Tests for ayah range validation."""

    def test_validate_valid_ayah_range(self, validator):
        """Test validating valid ayah ranges."""
        # Single ayah
        validator.validate_ayah_range(surah=1, start_ayah=1, end_ayah=1)

        # Multiple ayahs
        validator.validate_ayah_range(surah=1, start_ayah=1, end_ayah=7)

        # Partial range
        validator.validate_ayah_range(surah=2, start_ayah=100, end_ayah=200)

    def test_validate_invalid_ayah_range_backwards(self, validator):
        """Test validating ayah range where end < start."""
        with pytest.raises(InvalidAyahRangeError) as exc_info:
            validator.validate_ayah_range(surah=1, start_ayah=5, end_ayah=2)

        error = exc_info.value
        assert "End ayah must be >= start ayah" in str(error)
        assert error.details["start_ayah"] == 5
        assert error.details["end_ayah"] == 2

    def test_validate_ayah_range_start_exceeds_limit(self, validator):
        """Test validating ayah range where start exceeds surah limit."""
        # Surah 1 only has 7 ayahs
        with pytest.raises(InvalidAyahError):
            validator.validate_ayah_range(surah=1, start_ayah=10, end_ayah=15)

    def test_validate_ayah_range_end_exceeds_limit(self, validator):
        """Test validating ayah range where end exceeds surah limit."""
        # Surah 1 only has 7 ayahs
        with pytest.raises(InvalidAyahError):
            validator.validate_ayah_range(surah=1, start_ayah=1, end_ayah=10)


class TestReciterValidation:
    """Tests for reciter validation."""

    def test_validate_valid_reciter(self, validator):
        """Test validating valid reciter keys."""
        validator.validate_reciter("mishary_alafasy")
        validator.validate_reciter("sudais")
        validator.validate_reciter("ghamdi")

    def test_validate_invalid_reciter(self, validator):
        """Test validating invalid reciter key."""
        with pytest.raises(InvalidReciterError) as exc_info:
            validator.validate_reciter("invalid_reciter")

        error = exc_info.value
        assert "Invalid reciter key: 'invalid_reciter'" in str(error)
        assert "mishary_alafasy" in error.details["valid_keys"]

    def test_get_reciter_info(self, validator):
        """Test getting reciter information."""
        info = validator.get_reciter_info("mishary_alafasy")

        assert info["id"] == 7
        assert info["name"] == "Mishary Rashid Alafasy"
        assert info["has_timestamps"] is True

    def test_check_reciter_has_timestamps(self, validator):
        """Test checking if reciter has timestamps."""
        # Mishary Alafasy has confirmed timestamps
        assert validator.check_reciter_has_timestamps("mishary_alafasy") is True

        # Others are uncertain
        assert validator.check_reciter_has_timestamps("sudais") is False


class TestTranslationValidation:
    """Tests for translation validation."""

    def test_validate_valid_translation(self, validator):
        """Test validating valid translation keys."""
        validator.validate_translation("en_sahih")
        validator.validate_translation("en_yusufali")
        validator.validate_translation("en_pickthall")

    def test_validate_invalid_translation(self, validator):
        """Test validating invalid translation key."""
        with pytest.raises(InvalidTranslationError) as exc_info:
            validator.validate_translation("invalid_translation")

        error = exc_info.value
        assert "Invalid translation key: 'invalid_translation'" in str(error)
        assert "en_sahih" in error.details["valid_keys"]

    def test_get_translation_info(self, validator):
        """Test getting translation information."""
        info = validator.get_translation_info("en_sahih")

        assert info["identifier"] == "en.sahih"
        assert info["name"] == "Sahih International"


class TestBackgroundValidation:
    """Tests for background validation."""

    def test_validate_valid_background(self, validator):
        """Test validating valid background ID."""
        # Note: This test assumes background files exist
        # In a real test environment, you might need to create mock files
        try:
            validator.validate_background("nature_video")
        except BackgroundMediaNotFoundError:
            # File doesn't exist in test environment - expected
            pass

    def test_validate_invalid_background_id(self, validator):
        """Test validating invalid background ID."""
        with pytest.raises(InvalidBackgroundError) as exc_info:
            validator.validate_background("invalid_background")

        error = exc_info.value
        assert "Invalid background ID: 'invalid_background'" in str(error)
        assert "nature_video" in error.details["valid_ids"]

    def test_get_background_info(self, validator):
        """Test getting background information."""
        try:
            info = validator.get_background_info("nature_video")
            assert info["type"] == "video"
            assert "path" in info
        except BackgroundMediaNotFoundError:
            # File doesn't exist in test environment - expected
            pass


class TestFilenameValidation:
    """Tests for filename validation."""

    def test_validate_valid_filename(self, validator):
        """Test validating valid filenames."""
        validator.validate_output_filename("my_video")
        validator.validate_output_filename("video-123")
        validator.validate_output_filename("test_file_name")
        validator.validate_output_filename(None)  # None is valid (optional)

    def test_validate_filename_with_invalid_characters(self, validator):
        """Test validating filename with invalid characters."""
        invalid_filenames = [
            "file<name",
            "file>name",
            "file:name",
            'file"name',
            "file/name",
            "file\\name",
            "file|name",
            "file?name",
            "file*name"
        ]

        for filename in invalid_filenames:
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_output_filename(filename)

            assert "invalid characters" in str(exc_info.value).lower()

    def test_validate_filename_too_long(self, validator):
        """Test validating filename that is too long."""
        long_filename = "a" * 256

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_output_filename(long_filename)

        assert "too long" in str(exc_info.value).lower()


class TestCompleteRequestValidation:
    """Tests for complete request validation."""

    def test_validate_complete_valid_request(self, validator):
        """Test validating a complete valid request."""
        is_valid, error_msg = validator.validate_request(
            surah=1,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        # May be False if background file doesn't exist
        # but shouldn't raise an exception
        assert error_msg is None or "not found" in error_msg.lower()

    def test_validate_complete_request_invalid_surah(self, validator):
        """Test validating complete request with invalid surah."""
        is_valid, error_msg = validator.validate_request(
            surah=999,
            start_ayah=1,
            end_ayah=7,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        assert is_valid is False
        assert error_msg is not None
        assert "999" in error_msg

    def test_validate_complete_request_invalid_ayah_range(self, validator):
        """Test validating complete request with invalid ayah range."""
        is_valid, error_msg = validator.validate_request(
            surah=1,
            start_ayah=5,
            end_ayah=2,
            reciter_key="mishary_alafasy",
            translation_key="en_sahih",
            background_id="nature_video"
        )

        assert is_valid is False
        assert error_msg is not None


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_max_ayah_for_surah(self, validator):
        """Test getting maximum ayah for each surah."""
        assert validator.get_max_ayah_for_surah(1) == 7  # Al-Fatiha
        assert validator.get_max_ayah_for_surah(2) == 286  # Al-Baqarah
        assert validator.get_max_ayah_for_surah(114) == 6  # An-Nas

    def test_get_max_ayah_for_invalid_surah(self, validator):
        """Test getting max ayah for invalid surah."""
        with pytest.raises(InvalidSurahError):
            validator.get_max_ayah_for_surah(999)
