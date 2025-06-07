# config.py
import os
from pathlib import Path

# --- Core Paths ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output_cli" # Separate output for CLI tool
TEMP_DIR = BASE_DIR / "temp_cli"
DATA_DIR = BASE_DIR / "data"
LOCAL_QURAN_ROOT_DIR = DATA_DIR / "quran_cache"
LOCAL_QURAN_TEXT_DIR = LOCAL_QURAN_ROOT_DIR / "text_and_words"
LOCAL_QURAN_TRANSLATIONS_DIR = LOCAL_QURAN_ROOT_DIR / "translations"
LOCAL_QURAN_TAFSEER_DIR = LOCAL_QURAN_ROOT_DIR / "tafseer" # New for Tafseer

# --- Ensure Directories Exist ---
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_QURAN_ROOT_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_QURAN_TEXT_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_QURAN_TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_QURAN_TAFSEER_DIR.mkdir(parents=True, exist_ok=True)


# --- API Settings ---
QURAN_COM_API_URL = "https://api.quran.com/api/v4"
ALQURAN_CLOUD_API_URL = "https://api.alquran.cloud/v1" # For translations if not cached
REQUEST_TIMEOUT = 45

# --- Number of ayahs per surah ---
SURAH_AYAHS_COUNT = [0, # Dummy for 0-index
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6
]

# --- Translation Mappings (AlQuran.Cloud Identifiers or Quran.com IDs) ---
TRANSLATION_INFO = {
    "en_sahih_qcom": { # Example using Quran.com translation ID
        "id": 131, # Sahih International (from quran.com translations endpoint)
        "type": "quran.com",
        "lang": "en",
        "name": "Sahih International (Quran.com)"
    },
    "en_pickthall_aqc": { # Example using AlQuran.Cloud
        "identifier": "en.pickthall",
        "type": "alquran.cloud",
        "name": "Pickthall (AlQuran.Cloud)"
    },
    # Add more as needed
}

# --- Tafseer Mappings (Quran.com Tafsir IDs) ---
# Find IDs from https://api.quran.com/api/v4/resources/tafsirs?language=en (or other languages)
TAFSEER_INFO = {
    "en_ibn_kathir": {
        "id": 169, # Tafsir Ibn Kathir (English from quran.com)
        "lang": "en",
        "name": "Tafsir Ibn Kathir (English)"
    },
    "ar_muyassar": {
        "id": 167, # Tafseer Al Muyassar (Arabic)
        "lang": "ar",
        "name": "Tafseer Al Muyassar (Arabic)"
    }
    # Add more as needed
}