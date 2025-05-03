# data_loader.py
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import requests

from config import (
    QURAN_COM_API_URL, ALQURAN_CLOUD_API_URL, RECITER_INFO,
    TRANSLATION_INFO, REQUEST_TIMEOUT, TEMP_DIR
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API-related errors."""
    pass

# --- (fetch_quran_data_from_api remains the same) ---
def fetch_quran_data_from_api(
    surah: int,
    ayah: int,
    reciter_id_numeric: int
) -> Dict[str, Any]:
    """
    Fetches Arabic text, word list, timestamps, and audio URL for a SINGLE Ayah
    from api.quran.com.
    """
    verse_key = f"{surah}:{ayah}"
    url = f"{QURAN_COM_API_URL}/verses/by_key/{verse_key}"
    params = {
        "words": "true",
        "word_fields": "text_uthmani",
        "audio": reciter_id_numeric,
        "fields": "text_uthmani"
    }
    log.info(f"Fetching verse data from Quran.com: {url} with params {params}")

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if "verse" not in data:
            raise APIError(f"API response missing 'verse' key for {verse_key}")

        verse_data = data["verse"]

        # Validate essential fields that should always be there
        if "text_uthmani" not in verse_data:
             raise APIError(f"API response missing 'text_uthmani' for {verse_key}")
        # Don't fail immediately if words/audio are missing, let parsing handle it
        # if "words" not in verse_data: ...
        # if not verse_data.get("audio", {}).get("url"): ...

        log.info(f"Successfully fetched verse data for {verse_key}")
        return verse_data

    except requests.exceptions.RequestException as e:
        log.error(f"API request failed for {verse_key}: {e}")
        raise APIError(f"Network or API error fetching verse data: {e}")
    except Exception as e:
        log.error(f"Unexpected error processing API response for {verse_key}: {e}")
        raise APIError(f"Failed to process API data: {e}")


def get_arabic_text_and_timestamps(
    verse_data: Dict[str, Any]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts the full Arabic text and word timestamps from the fetched verse data.
    Prefers direct word timestamps (timestamp_from/to).
    Falls back to using audio segment timings if direct ones are unavailable.
    Converts timestamps from milliseconds to seconds.
    """
    full_arabic_text = verse_data.get("text_uthmani", "")
    words_data = verse_data.get("words", [])
    ayah_timestamps = []

    if not words_data:
        log.warning("No words data found in API response.")
        return full_arabic_text, []

    # --- Strategy: Try direct timestamps first, then fallback to segments ---

    # Check if *any* word has direct timestamps
    has_direct_timestamps = False
    for word in words_data:
        if word.get("timestamp_from") is not None and word.get("timestamp_to") is not None:
            has_direct_timestamps = True
            break

    if has_direct_timestamps:
        log.debug("Using direct word timestamps (timestamp_from / timestamp_to)")
        for i, word in enumerate(words_data):
            start_ms = word.get("timestamp_from")
            end_ms = word.get("timestamp_to")
            word_text = word.get("text_uthmani")

            if start_ms is not None and end_ms is not None and word_text is not None:
                ayah_timestamps.append({
                    "word_index": i,
                    "text": word_text,
                    "start_time": start_ms / 1000.0, # Convert ms to seconds
                    "end_time": end_ms / 1000.0
                })
            else:
                # Log missing data for a specific word *only if* we expected direct timestamps
                log.warning(f"Missing direct timestamp/text for word index {i} in verse '{verse_data.get('verse_key', '')}'. Skipping word.")
    else:
        # Fallback: Try using segment data if no direct timestamps were found
        segments = verse_data.get("audio", {}).get("segments", [])
        if segments:
            log.debug(f"Using audio segment timings as fallback for verse '{verse_data.get('verse_key', '')}'")
            # Create a mapping from word index to its segment time
            word_index_to_timing = {}
            try:
                for segment_data in segments:
                    # Format seems: [word_start_index, word_end_index?, start_ms, end_ms]
                    # Assuming the first element is the 0-based word index this segment applies to.
                    # This is a simplification; a segment might cover multiple words.
                    # A more robust approach would be needed if timings aren't 1:1 with words.
                    if len(segment_data) == 4:
                         word_idx = int(segment_data[0]) # Assuming 0-based index
                         start_ms = int(segment_data[2])
                         end_ms = int(segment_data[3])
                         if word_idx >= 0: # Basic sanity check
                              word_index_to_timing[word_idx] = (start_ms / 1000.0, end_ms / 1000.0)
                         else:
                              log.warning(f"Invalid segment word index found: {word_idx}")
                    else:
                         log.warning(f"Unexpected segment format: {segment_data}")

                # Now, map these timings back to the words list
                for i, word in enumerate(words_data):
                    word_text = word.get("text_uthmani")
                    timing = word_index_to_timing.get(i)

                    if timing and word_text:
                        start_time, end_time = timing
                        ayah_timestamps.append({
                            "word_index": i,
                            "text": word_text,
                            "start_time": start_time,
                            "end_time": end_time
                        })
                    else:
                        log.warning(f"Could not find segment timing or text for word index {i} in verse '{verse_data.get('verse_key', '')}'. Skipping word (segment mode).")

            except (ValueError, TypeError) as e:
                log.error(f"Error parsing segment data for verse '{verse_data.get('verse_key', '')}': {e}. Segments: {segments}")

        else:
             log.warning(f"No direct timestamps and no audio segment data found for verse '{verse_data.get('verse_key', '')}'. Cannot determine timings.")

    # Final check if timestamps list is populated
    if not ayah_timestamps and words_data:
        log.warning(f"Could not parse any valid timestamps for verse '{verse_data.get('verse_key', '')}' using direct or segment methods.")
    elif ayah_timestamps:
        log.info(f"Successfully parsed {len(ayah_timestamps)} word timestamps for verse '{verse_data.get('verse_key', '')}'.")


    return full_arabic_text, ayah_timestamps


# --- (get_translation_text_from_api remains the same) ---
def get_translation_text_from_api(
    surah: int,
    ayah: int,
    translation_identifier: str # e.g., "en.sahih"
) -> str:
    """
    Fetches translation text for a SINGLE Ayah from api.alquran.cloud.
    """
    ayah_ref = f"{surah}:{ayah}"
    url = f"{ALQURAN_CLOUD_API_URL}/ayah/{ayah_ref}/{translation_identifier}"
    log.info(f"Fetching translation from AlQuran.Cloud: {url}")

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 200 and "data" in data and "text" in data["data"]:
            translation = data["data"]["text"]
            log.info(f"Successfully fetched translation for {ayah_ref}")
            return translation
        else:
            error_detail = data.get("data", "Unknown error from AlQuran.Cloud API")
            raise APIError(f"AlQuran.Cloud API did not return successful data: {error_detail}")

    except requests.exceptions.RequestException as e:
        log.error(f"API request failed for translation {ayah_ref}: {e}")
        raise APIError(f"Network or API error fetching translation: {e}")
    except Exception as e:
        log.error(f"Unexpected error processing translation API response for {ayah_ref}: {e}")
        raise APIError(f"Failed to process translation API data: {e}")


# --- (download_audio_temporarily remains the same) ---
def download_audio_temporarily(audio_url: str, job_id: str) -> Optional[Path]:
    """
    Downloads audio from the URL to a temporary file.
    Returns the path to the temporary file or None on failure.
    """
    if not audio_url:
        log.error("No audio URL provided for download.")
        return None

    try:
        # Use tempfile module for better cross-platform compatibility and management
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=TEMP_DIR, prefix=f"{job_id}_") as temp_file:
            temp_audio_path = Path(temp_file.name)

        log.info(f"[Job {job_id}] Downloading audio from {audio_url} to {temp_audio_path}")
        response = requests.get(audio_url, stream=True, timeout=REQUEST_TIMEOUT * 2) # Longer timeout for download
        response.raise_for_status()

        with open(temp_audio_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        log.info(f"[Job {job_id}] Audio downloaded successfully to {temp_audio_path}")
        return temp_audio_path

    except requests.exceptions.RequestException as e:
        log.error(f"[Job {job_id}] Failed to download audio from {audio_url}: {e}")
        if 'temp_audio_path' in locals() and temp_audio_path.exists():
            try: temp_audio_path.unlink()
            except OSError: pass
        return None
    except Exception as e:
        log.error(f"[Job {job_id}] Unexpected error downloading audio: {e}")
        if 'temp_audio_path' in locals() and temp_audio_path.exists():
            try: temp_audio_path.unlink()
            except OSError: pass
        return None