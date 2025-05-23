# config.py
import os
from pathlib import Path

# --- Core Paths ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp" # For temporary downloads, intermediate files
DATA_DIR = BASE_DIR / "data" # For local data like backgrounds, fonts
FONTS_DIR = DATA_DIR / "fonts"
SAMPLE_BACKGROUNDS_DIR = DATA_DIR / "sample_backgrounds"

# --- Ensure Directories Exist ---
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True) # Ensure fonts dir exists
SAMPLE_BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)

# --- API Settings ---
QURAN_COM_API_URL = "https://api.quran.com/api/v4"
QURAN_COM_AUDIO_BASE_URL = "https://verses.quran.com/"
ALQURAN_CLOUD_API_URL = "https://api.alquran.cloud/v1"
REQUEST_TIMEOUT = 45 # Seconds for API requests (increased slightly)

# --- Reciter Mappings (Quran.com IDs) ---
# Map user-friendly names to Quran.com numeric reciter IDs.
# *IMPORTANT*: Word-level timestamps are ESSENTIAL. Only ID 7 (Alafasy) is widely confirmed.
# You MUST verify timestamp availability via API testing for other reciters before relying on them.
# Check IDs: https://quran.com/api/docs/getting-started -> Recitations
RECITER_INFO = {
    "mishary_alafasy": {
        "id": 7, # Mishary Rashid Alafasy [Word Timestamps CONFIRMED]
        "name": "Mishary Rashid Alafasy"
    },
    "abdulbaset_mujawwad": {
        "id": 2, # AbdulBaset AbdulSamad (Mujawwad) [Word Timestamps UNCERTAIN - TEST!]
        "name": "AbdulBaset AbdulSamad (Mujawwad)"
    },
     "sudais": {
        "id": 3, # [Word Timestamps UNCERTAIN - TEST!]
        "name": "Abdur-Rahman as-Sudais"
    },
    "husary_mujawwad": {
        "id": 8, # Mahmoud Khalil Al-Hussary (Mujawwad) [Word Timestamps UNCERTAIN - TEST!]
        "name": "Mahmoud Khalil Al-Hussary"
    },
    "shatri": {
        "id": 4, # Abu Bakr al-Shatri [Word Timestamps UNCERTAIN - TEST!]
        "name": "Abu Bakr al-Shatri"
    },
     "shuraim": {
        "id": 12, # Sa`ud Ash-Shuraym [Word Timestamps UNCERTAIN - TEST!]
        "name": "Sa`ud Ash-Shuraym"
    },
    "ghamdi": {
        "id": 11, # Saad Al-Ghamdi [Word Timestamps UNCERTAIN - TEST!]
        "name": "Saad Al-Ghamdi"
     },
    "minshawi_mujawwad": {
        "id": 10, # Muhammad Siddiq Al-Minshawi (Mujawwad) [Word Timestamps UNCERTAIN - TEST!]
        "name": "Muhammad Siddiq Al-Minshawi (Mujawwad)"
    },
    "ajamy": {
        "id": 6, # Ahmed ibn Ali al-Ajamy [Word Timestamps UNCERTAIN - TEST!]
        "name": "Ahmed ibn Ali al-Ajamy"
    },
    "rifai": {
        "id": 9, # Hani Ar-Rifai [Word Timestamps UNCERTAIN - TEST!]
        "name": "Hani Ar-Rifai"
    },
    "basfar": {
        "id": 1, # Abdullah Basfar [Word Timestamps UNCERTAIN - TEST!]
        "name": "Abdullah Basfar"
    },
    "shaatree": {
        "id": 5, # Abu Bakr Ash-Shaatree [Word Timestamps UNCERTAIN - TEST!]
        "name": "Abu Bakr Ash-Shaatree"
    },
    "tablawy": {
        "id": 13, # Mohamed El-Tablawi [Word Timestamps UNCERTAIN - TEST!]
        "name": "Mohamed El-Tablawi"
    },
     "dussary": {
        "id": 15, # Yasser Ad-Dussary [Word Timestamps UNCERTAIN - TEST!]
        "name": "Yasser Ad-Dussary"
    },
    # Add others even more cautiously only after thorough API testing confirms word timestamps.
}

# --- Translation Mappings (AlQuran.Cloud Identifiers) ---
# Check identifiers: https://alquran.cloud/api/docs/translation
TRANSLATION_INFO = {
    "en_sahih": {
        "identifier": "en.sahih", # Sahih International
        "name": "Sahih International"
    },
    "en_pickthall": {
        "identifier": "en.pickthall", # Pickthall
        "name": "Pickthall"
    },
    "en_yusufali": {
        "identifier": "en.yusufali", # Yusuf Ali
        "name": "Abdullah Yusuf Ali"
    },
    "en_hilali": {
        "identifier": "en.hilali", # Hilali & Khan
        "name": "Hilali & Khan"
    },
    "en_arberry": {
        "identifier": "en.arberry", # A. J. Arberry
        "name": "A. J. Arberry"
    },
    "en_daryabadi": {
        "identifier": "en.daryabadi", # Daryabadi
        "name": "Abdul Majid Daryabadi"
    },
    "en_transliteration": {
        "identifier": "en.transliteration", # Roman Transliteration
        "name": "English Transliteration"
    },
    # Add other languages/translations as needed
    # "fr_hamidullah": {
    #     "identifier": "fr.hamidullah", # French: Muhammad Hamidullah
    #     "name": "French - Hamidullah"
    # },
    # "es_cortes": {
    #     "identifier": "es.cortes", # Spanish: Julio Cortes
    #     "name": "Spanish - Cortes"
    # }
}

# --- Background Mappings (Using Local Files) ---
# Ensure the files exist in the SAMPLE_BACKGROUNDS_DIR
BACKGROUND_MAP = {
    "nature_video": {
        "type": "video",
        "path": SAMPLE_BACKGROUNDS_DIR / "nature.mp4" # Make sure nature.mp4 exists
    },
    "calm_image": {
        "type": "image",
        "path": SAMPLE_BACKGROUNDS_DIR / "calm_image.jpeg" # Make sure calm_image.jpeg exists
    },
    "space_nebula": {
        "type": "video",
        "path": SAMPLE_BACKGROUNDS_DIR / "space_nebula.mp4" # Add space_nebula.mp4 if desired
    },
     "geometric_pattern": {
        "type": "image",
        "path": SAMPLE_BACKGROUNDS_DIR / "geometric_pattern.png" # Add geometric_pattern.png if desired
    },
     "kaaba_blur": {
        "type": "image",
        "path": SAMPLE_BACKGROUNDS_DIR / "kaaba_blur.jpg" # Add a suitable blurred Kaaba image
    }
    # Add more backgrounds as needed
}


# --- Video Generation Settings ---
# ** Important: Place the chosen font file (e.g., Amiri-Regular.ttf) in the data/fonts directory **
DEFAULT_FONT_ARABIC = str(FONTS_DIR / "Amiri" / "Amiri-Bold.ttf") # Recommended: Amiri
# DEFAULT_FONT_ARABIC = str(FONTS_DIR / "NotoNaskhArabic-Regular.ttf") # Alternative: Noto Naskh
DEFAULT_FONT_ENGLISH = str(FONTS_DIR / "Noto_Sans" / "NotoSans-Italic-VariableFont_wdth,wght.ttf") # Recommended: Noto Sans (download if needed)
# DEFAULT_FONT_ENGLISH = str(FONTS_DIR / "Arial.ttf") # Alternative: Arial (usually system available)

DEFAULT_FONT_SIZE_ARABIC = 48 # Adjust based on visual testing
DEFAULT_FONT_SIZE_ENGLISH = 36 # Adjust based on visual testing
DEFAULT_TEXT_COLOR = "white"

VIDEO_FPS = 24 # Frames per second
VIDEO_CODEC = "libx264" # Standard H.264 video codec
AUDIO_CODEC = "aac" # Standard audio codec for MP4 containers
AUDIO_CROSSFADE_MS = 150 # Crossfade duration in milliseconds (adjust as needed, 100-200ms is common)