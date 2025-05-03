# config.py
import os
from pathlib import Path

# --- Core Paths ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp" # For temporary downloads
DATA_DIR = BASE_DIR / "data" # Only for local data like backgrounds
SAMPLE_BACKGROUNDS_DIR = DATA_DIR / "sample_backgrounds"

# --- Ensure Directories Exist ---
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)

# --- API Settings ---
QURAN_COM_API_URL = "https://api.quran.com/api/v4"
QURAN_COM_AUDIO_BASE_URL = "https://verses.quran.com/"
ALQURAN_CLOUD_API_URL = "https://api.alquran.cloud/v1"

# --- Reciter Mappings (Crucial for Quran.com API) ---
# Map user-friendly names to Quran.com numeric reciter IDs
# IMPORTANT: Only include reciters known to have word-level timestamps on api.quran.com
# Check https://quran.com/api/docs/getting-started -> Recitations for IDs
RECITER_INFO = {
    "mishary_alafasy": {
        "id": 7, # Mishary Rashid Alafasy ID on Quran.com
        "name": "Mishary Rashid Alafasy"
    },
    # Add other reciters WITH TIMESTAMPS if you find their IDs
    # Example (needs verification if timestamps exist for him):
    # "abdul_basit": {
    #     "id": 2, # AbdulBaset AbdulSamad (Mujawwad) ID
    #     "name": "AbdulBaset AbdulSamad (Mujawwad)"
    # }
}

# --- Translation Mappings (Using AlQuran.Cloud Identifiers) ---
# Check https://alquran.cloud/api/docs/translation
TRANSLATION_INFO = {
    "en_sahih": {
        "identifier": "en.sahih", # Sahih International on AlQuran.Cloud
        "name": "Sahih International"
    },
    "en_pickthall": {
        "identifier": "en.pickthall",
        "name": "Pickthall"
    },
    # Add other translations
}

# --- Background Mappings (Using Local Files) ---
BACKGROUND_MAP = {
    "nature_video": {
        "type": "video",
        "path": SAMPLE_BACKGROUNDS_DIR / "nature.mp4"
    },
    "calm_image": {
        "type": "image",
        "path": SAMPLE_BACKGROUNDS_DIR / "calm_image.jpeg" # Add a sample image here
    }
    # Add other backgrounds
}


# --- Video Generation Settings ---
DEFAULT_FONT_ARABIC = "data/fonts/Arial.ttf"
DEFAULT_FONT_ENGLISH = "data/fonts/Arial.ttf"
DEFAULT_FONT_SIZE_ARABIC = 48
DEFAULT_FONT_SIZE_ENGLISH = 36
DEFAULT_TEXT_COLOR = "white"
VIDEO_FPS = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
REQUEST_TIMEOUT = 30 # Seconds for API requests