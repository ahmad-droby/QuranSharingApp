# data_loader.py
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import httpx
import asyncio

from config import (
    QURAN_COM_API_URL, ALQURAN_CLOUD_API_URL, REQUEST_TIMEOUT,
    LOCAL_QURAN_TEXT_DIR, LOCAL_QURAN_TRANSLATIONS_DIR, LOCAL_QURAN_TAFSEER_DIR, # Added TAFSEER_DIR
    TRANSLATION_INFO, TAFSEER_INFO
)

log = logging.getLogger(__name__)

class APIError(Exception):
    pass

# --- Quran Text (Uthmani & Words) ---
def get_ayah_text_and_words_from_cache_sync(surah: int, ayah: int) -> Optional[Dict[str, Any]]:
    # ... (same as before)
    cache_file = LOCAL_QURAN_TEXT_DIR / f"surah_{surah}.json"
    if not cache_file.exists(): return None
    try:
        with open(cache_file, 'r', encoding='utf-8') as f: surah_data = json.load(f)
        ayah_data = surah_data.get(str(ayah))
        if ayah_data and "text_uthmani" in ayah_data and "words" in ayah_data:
            return {"text_uthmani": ayah_data["text_uthmani"], "words": ayah_data["words"]}
        return None
    except (IOError, json.JSONDecodeError) as e:
        log.error(f"Err reading text cache {cache_file} for S{surah}:A{ayah}: {e}")
        return None

async def fetch_quran_data_from_api_core(surah: int, ayah: int) -> Optional[Dict[str, Any]]:
    """Core fetcher for text_uthmani and words (for caching). Reciter ID not needed here."""
    api_url = f"{QURAN_COM_API_URL}/verses/by_key/{surah}:{ayah}"
    params = {"words": "true", "word_fields": "text_uthmani,char_type_name,offset_start,offset_end", "fields": "text_uthmani"}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            verse_data = data.get("verse", data.get("verses", [{}])[0] if data.get("verses") else {})
            if verse_data and "text_uthmani" in verse_data: return verse_data
            log.error(f"Verse data malformed for S{surah}:A{ayah} from {api_url}")
            return None
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
        log.error(f"API/Request/JSON err for S{surah}:A{ayah} text: {e}")
        raise APIError(f"API error for S{surah}:A{ayah} text: {e}") from e

async def get_quran_ayah_ground_truth(surah: int, ayah: int, force_api: bool = False) -> Optional[Dict[str, Any]]:
    # ... (same as before, but uses fetch_quran_data_from_api_core)
    if not force_api:
        cached = get_ayah_text_and_words_from_cache_sync(surah, ayah)
        if cached: return cached
    try:
        api_data = await fetch_quran_data_from_api_core(surah, ayah)
        if api_data and "text_uthmani" in api_data and "words" in api_data:
            words = [
                {"text_uthmani": w.get("text_uthmani"), "char_type_name": w.get("char_type_name"),
                 "char_offset_start": w.get("char_offset_start"), "char_offset_end": w.get("char_offset_end")}
                for w in api_data.get("words", []) if w.get("char_type_name") == "word"
            ]
            return {"text_uthmani": api_data["text_uthmani"], "words": words}
        return None
    except APIError as e:
        log.error(f"APIError fetching GT for S{surah}:A{ayah}: {e}")
        return None


# --- Translations ---
async def fetch_translation_from_quran_com(surah: int, ayah: int, translation_id: int) -> Optional[str]:
    api_url = f"{QURAN_COM_API_URL}/quran/translations/{translation_id}"
    params = {"verse_key": f"{surah}:{ayah}"}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            # Translations from quran.com are often nested
            if "translations" in data and data["translations"]:
                return data["translations"][0].get("text")
            log.warning(f"Translation {translation_id} not found for S{surah}:A{ayah} in quran.com response.")
            return None
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
        log.error(f"API/Request/JSON err for quran.com trans {translation_id}, S{surah}:A{ayah}: {e}")
        raise APIError(f"API error for quran.com trans {translation_id}, S{surah}:A{ayah}: {e}") from e

async def fetch_translation_from_alquran_cloud(surah: int, ayah: int, identifier: str) -> Optional[str]:
    api_url = f"{ALQURAN_CLOUD_API_URL}/ayah/{surah}:{ayah}/{identifier}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 200 and "data" in data and "text" in data["data"]: return data["data"]["text"]
            log.warning(f"Translation {identifier} not found for S{surah}:A{ayah} in alquran.cloud response: {data.get('status')}")
            return None
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
        log.error(f"API/Request/JSON err for alquran.cloud trans {identifier}, S{surah}:A{ayah}: {e}")
        raise APIError(f"API error for alquran.cloud trans {identifier}, S{surah}:A{ayah}: {e}") from e

async def get_translation_text_cached(surah: int, ayah: int, translation_key: str, force_api: bool = False) -> Optional[str]:
    # ... (modified to handle different translation types)
    trans_info = TRANSLATION_INFO.get(translation_key)
    if not trans_info:
        log.error(f"Translation key '{translation_key}' not found in TRANSLATION_INFO.")
        return None

    fs_safe_key = translation_key.replace('.', '_') # For directory naming
    cache_dir = LOCAL_QURAN_TRANSLATIONS_DIR / fs_safe_key
    cache_file = cache_dir / f"surah_{surah}.json"

    if not force_api and cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f: surah_translations = json.load(f)
            text = surah_translations.get(str(ayah))
            if text is not None: return text
        except (IOError, json.JSONDecodeError) as e:
            log.error(f"Error reading trans cache {cache_file} for S{surah}:A{ayah}: {e}")

    log.debug(f"Trans cache miss for {translation_key} S{surah}:A{ayah}. Fetching from API.")
    try:
        if trans_info["type"] == "quran.com":
            return await fetch_translation_from_quran_com(surah, ayah, trans_info["id"])
        elif trans_info["type"] == "alquran.cloud":
            return await fetch_translation_from_alquran_cloud(surah, ayah, trans_info["identifier"])
        else:
            log.error(f"Unsupported translation type for key '{translation_key}': {trans_info['type']}")
            return None
    except APIError: return None # Error already logged by fetchers


# --- Tafseer ---
async def fetch_tafseer_from_quran_com(surah: int, ayah: int, tafseer_id: int) -> Optional[str]:
    # Quran.com API for tafsir: /quran/tafsirs/{tafsir_id}?verse_key={verse_key}
    api_url = f"{QURAN_COM_API_URL}/quran/tafsirs/{tafseer_id}"
    params = {"verse_key": f"{surah}:{ayah}"}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            # Tafsir from quran.com is nested
            if "tafsirs" in data and data["tafsirs"]:
                # The text might be HTML, needs stripping if plain text is desired
                return data["tafsirs"][0].get("text")
            log.warning(f"Tafsir {tafseer_id} not found for S{surah}:A{ayah} in quran.com response.")
            return None
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
        log.error(f"API/Request/JSON err for tafsir {tafseer_id}, S{surah}:A{ayah}: {e}")
        raise APIError(f"API error for tafsir {tafseer_id}, S{surah}:A{ayah}: {e}") from e

async def get_tafseer_text_cached(surah: int, ayah: int, tafseer_key: str, force_api: bool = False) -> Optional[str]:
    tafseer_info = TAFSEER_INFO.get(tafseer_key)
    if not tafseer_info:
        log.error(f"Tafseer key '{tafseer_key}' not found in TAFSEER_INFO.")
        return None

    fs_safe_key = tafseer_key.replace('.', '_')
    cache_dir = LOCAL_QURAN_TAFSEER_DIR / fs_safe_key
    cache_file = cache_dir / f"surah_{surah}.json"

    if not force_api and cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f: surah_tafseer = json.load(f)
            text = surah_tafseer.get(str(ayah))
            if text is not None: return text
        except (IOError, json.JSONDecodeError) as e:
            log.error(f"Error reading tafseer cache {cache_file} for S{surah}:A{ayah}: {e}")

    log.debug(f"Tafseer cache miss for {tafseer_key} S{surah}:A{ayah}. Fetching from API.")
    try:
        # Assuming all tafseer currently comes from Quran.com based on TAFSEER_INFO structure
        return await fetch_tafseer_from_quran_com(surah, ayah, tafseer_info["id"])
    except APIError: return None


# --- Cache Population (Can be called from a separate admin script or FastAPI endpoint) ---
# Functions like `_populate_single_surah_text_cache`, `populate_quran_text_cache_job_internal`
# `_populate_single_surah_translation_cache`, `populate_quran_translation_cache_job_internal`
# can be defined here. For the standalone script, these might be run manually or
# the script will just rely on API if cache is empty.
# For brevity, I'll omit the full cache population functions here, but they'd be similar
# to what was in `main.py`, adapted to use the fetchers in this `data_loader.py`.
# A new one for tafseer would be:
async def _populate_single_surah_tafseer_cache(surah_num: int, taf_key: str, taf_id: int, session: httpx.AsyncClient):
    # ... similar logic to translation caching ...
    # Call fetch_tafseer_from_quran_com
    # Save to LOCAL_QURAN_TAFSEER_DIR / taf_key_fs_safe / f"surah_{surah_num}.json"
    pass

async def populate_quran_tafseer_cache_job_internal(tafseer_key_filter: Optional[str] = None):
    # ... similar logic to translation caching ...
    pass