# config_new.py
"""
Improved configuration management with environment variable support.

This module provides centralized configuration with proper validation,
environment variable overrides, and structured settings management.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PathConfig:
    """Configuration for file system paths."""
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    output_dir: Optional[Path] = None
    temp_dir: Optional[Path] = None
    data_dir: Optional[Path] = None
    fonts_dir: Optional[Path] = None
    sample_backgrounds_dir: Optional[Path] = None
    database_path: Optional[Path] = None

    def __post_init__(self):
        """Set default paths and ensure directories exist."""
        self.output_dir = self.output_dir or self.base_dir / "output"
        self.temp_dir = self.temp_dir or self.base_dir / "temp"
        self.data_dir = self.data_dir or self.base_dir / "data"
        self.fonts_dir = self.fonts_dir or self.data_dir / "fonts"
        self.sample_backgrounds_dir = self.sample_backgrounds_dir or self.data_dir / "sample_backgrounds"
        self.database_path = self.database_path or self.base_dir / "quran_video_jobs.db"

        # Create directories
        for dir_path in [
            self.output_dir,
            self.temp_dir,
            self.data_dir,
            self.fonts_dir,
            self.sample_backgrounds_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class APIConfig:
    """Configuration for external API endpoints."""
    quran_com_url: str = "https://api.quran.com/api/v4"
    quran_com_audio_base_url: str = "https://verses.quran.com/"
    alquran_cloud_url: str = "https://api.alquran.cloud/v1"
    request_timeout: int = 45  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds


@dataclass
class VideoConfig:
    """Configuration for video generation settings."""
    fps: int = 24
    codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "5000k"
    preset: str = "medium"
    font_arabic: str = "Amiri-Bold.ttf"
    font_english: str = "NotoSans-Italic-VariableFont_wdth,wght.ttf"
    font_size_arabic: int = 48
    font_size_english: int = 36
    text_color: str = "white"
    audio_crossfade_ms: int = 150
    audio_padding_ms: int = 100

    def get_arabic_font_path(self, fonts_dir: Path) -> str:
        """Get full path to Arabic font."""
        return str(fonts_dir / "Amiri" / self.font_arabic)

    def get_english_font_path(self, fonts_dir: Path) -> str:
        """Get full path to English font."""
        return str(fonts_dir / "Noto_Sans" / self.font_english)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    enabled: bool = True
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 50
    max_concurrent_jobs: int = 3


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    max_age_days: int = 7
    cleanup_interval_hours: int = 24


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None


class Config:
    """
    Main configuration class that aggregates all settings.

    This class loads configuration from environment variables and provides
    a unified interface for accessing all application settings.
    """

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.paths = PathConfig()
        self.api = APIConfig(
            quran_com_url=os.getenv("QURAN_COM_API_URL", "https://api.quran.com/api/v4"),
            quran_com_audio_base_url=os.getenv("QURAN_COM_AUDIO_BASE_URL", "https://verses.quran.com/"),
            alquran_cloud_url=os.getenv("ALQURAN_CLOUD_API_URL", "https://api.alquran.cloud/v1"),
            request_timeout=int(os.getenv("API_REQUEST_TIMEOUT", "45")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("API_RETRY_DELAY", "1.0"))
        )
        self.video = VideoConfig(
            fps=int(os.getenv("VIDEO_FPS", "24")),
            codec=os.getenv("VIDEO_CODEC", "libx264"),
            audio_codec=os.getenv("AUDIO_CODEC", "aac"),
            bitrate=os.getenv("VIDEO_BITRATE", "5000k"),
            preset=os.getenv("VIDEO_PRESET", "medium"),
            font_size_arabic=int(os.getenv("FONT_SIZE_ARABIC", "48")),
            font_size_english=int(os.getenv("FONT_SIZE_ENGLISH", "36")),
            text_color=os.getenv("TEXT_COLOR", "white"),
            audio_crossfade_ms=int(os.getenv("AUDIO_CROSSFADE_MS", "150")),
            audio_padding_ms=int(os.getenv("AUDIO_PADDING_MS", "100"))
        )
        self.rate_limit = RateLimitConfig(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            max_requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
            max_requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "50")),
            max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
        )
        self.cache = CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            max_age_days=int(os.getenv("CACHE_MAX_AGE_DAYS", "7")),
            cleanup_interval_hours=int(os.getenv("CACHE_CLEANUP_INTERVAL_HOURS", "24"))
        )
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv(
                "LOG_FORMAT",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

        # Database configuration
        self.database_url = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{self.paths.database_path}"
        )
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # Load reciter and translation mappings
        self.reciters = self._load_reciter_info()
        self.translations = self._load_translation_info()
        self.backgrounds = self._load_background_map()

        # Surah ayah counts for validation
        self.surah_ayah_counts = SURAH_AYAH_COUNTS

    def _load_reciter_info(self) -> Dict[str, Dict[str, Any]]:
        """Load reciter mappings."""
        return {
            "mishary_alafasy": {
                "id": 7,
                "name": "Mishary Rashid Alafasy",
                "has_timestamps": True  # CONFIRMED
            },
            "abdulbaset_mujawwad": {
                "id": 2,
                "name": "AbdulBaset AbdulSamad (Mujawwad)",
                "has_timestamps": False  # UNCERTAIN
            },
            "sudais": {
                "id": 3,
                "name": "Abdur-Rahman as-Sudais",
                "has_timestamps": False  # UNCERTAIN
            },
            "husary_mujawwad": {
                "id": 8,
                "name": "Mahmoud Khalil Al-Hussary",
                "has_timestamps": False  # UNCERTAIN
            },
            "shatri": {
                "id": 4,
                "name": "Abu Bakr al-Shatri",
                "has_timestamps": False  # UNCERTAIN
            },
            "shuraim": {
                "id": 12,
                "name": "Sa`ud Ash-Shuraym",
                "has_timestamps": False  # UNCERTAIN
            },
            "ghamdi": {
                "id": 11,
                "name": "Saad Al-Ghamdi",
                "has_timestamps": False  # UNCERTAIN
            },
            "minshawi_mujawwad": {
                "id": 10,
                "name": "Muhammad Siddiq Al-Minshawi (Mujawwad)",
                "has_timestamps": False  # UNCERTAIN
            },
            "ajamy": {
                "id": 6,
                "name": "Ahmed ibn Ali al-Ajamy",
                "has_timestamps": False  # UNCERTAIN
            },
            "rifai": {
                "id": 9,
                "name": "Hani Ar-Rifai",
                "has_timestamps": False  # UNCERTAIN
            },
            "basfar": {
                "id": 1,
                "name": "Abdullah Basfar",
                "has_timestamps": False  # UNCERTAIN
            },
            "shaatree": {
                "id": 5,
                "name": "Abu Bakr Ash-Shaatree",
                "has_timestamps": False  # UNCERTAIN
            },
            "tablawy": {
                "id": 13,
                "name": "Mohamed El-Tablawi",
                "has_timestamps": False  # UNCERTAIN
            },
            "dussary": {
                "id": 15,
                "name": "Yasser Ad-Dussary",
                "has_timestamps": False  # UNCERTAIN
            },
        }

    def _load_translation_info(self) -> Dict[str, Dict[str, str]]:
        """Load translation mappings."""
        return {
            "en_sahih": {
                "identifier": "en.sahih",
                "name": "Sahih International"
            },
            "en_pickthall": {
                "identifier": "en.pickthall",
                "name": "Pickthall"
            },
            "en_yusufali": {
                "identifier": "en.yusufali",
                "name": "Abdullah Yusuf Ali"
            },
            "en_hilali": {
                "identifier": "en.hilali",
                "name": "Hilali & Khan"
            },
            "en_arberry": {
                "identifier": "en.arberry",
                "name": "A. J. Arberry"
            },
            "en_daryabadi": {
                "identifier": "en.daryabadi",
                "name": "Abdul Majid Daryabadi"
            },
            "en_transliteration": {
                "identifier": "en.transliteration",
                "name": "English Transliteration"
            },
        }

    def _load_background_map(self) -> Dict[str, Dict[str, Any]]:
        """Load background media mappings."""
        return {
            "nature_video": {
                "type": "video",
                "path": self.paths.sample_backgrounds_dir / "nature.mp4"
            },
            "calm_image": {
                "type": "image",
                "path": self.paths.sample_backgrounds_dir / "calm_image.jpeg"
            },
            "space_nebula": {
                "type": "video",
                "path": self.paths.sample_backgrounds_dir / "space_nebula.mp4"
            },
            "geometric_pattern": {
                "type": "image",
                "path": self.paths.sample_backgrounds_dir / "geometric_pattern.png"
            },
            "kaaba_blur": {
                "type": "image",
                "path": self.paths.sample_backgrounds_dir / "kaaba_blur.jpg"
            }
        }


# Quran Surah ayah counts for validation (1-114)
SURAH_AYAH_COUNTS = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109,
    11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135,
    21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
    31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85,
    41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
    51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
    61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
    71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42,
    81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20,
    91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
    101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
    111: 5, 112: 4, 113: 5, 114: 6
}


# Global configuration instance
# This can be imported by other modules: from config_new import config
config = Config()
