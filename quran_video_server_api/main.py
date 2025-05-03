# main.py
import logging
import uuid
import traceback
from pathlib import Path
from urllib.parse import urljoin
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, status, Request
# --- MODIFIED IMPORT ---
from pydantic import BaseModel, Field, validator, model_validator # Removed root_validator, added model_validator

from config import (
    OUTPUT_DIR, RECITER_INFO, TRANSLATION_INFO, BACKGROUND_MAP,
    QURAN_COM_AUDIO_BASE_URL, TEMP_DIR
)
from data_loader import (
    fetch_quran_data_from_api, get_arabic_text_and_timestamps,
    get_translation_text_from_api, download_audio_temporarily, APIError
)
from video_generator import generate_quran_video, concatenate_audio_files

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

app = FastAPI(
    title="Quran Video Generator API (API-Driven)",
    description="API to generate videos for a SINGLE or MULTIPLE consecutive AYAHs using public APIs for text, translation, audio, and timestamps.",
    version="0.3.0"
)

# --- Request Model (Multiple Ayahs) ---
class VideoRequest(BaseModel):
    surah: int = Field(..., gt=0, le=114, description="Surah number (1-114)")
    start_ayah: int = Field(..., gt=0, description="Starting Ayah number for the video range")
    end_ayah: int = Field(..., gt=0, description="Ending Ayah number for the video range (inclusive)")
    reciter_key: str = Field(..., description=f"Key of the reciter. Available: {list(RECITER_INFO.keys())}")
    translation_key: str = Field(..., description=f"Key of the translation. Available: {list(TRANSLATION_INFO.keys())}")
    background_id: str = Field(..., description=f"ID of the background. Available: {list(BACKGROUND_MAP.keys())}")
    output_filename: Optional[str] = Field(None, description="Optional custom filename (without extension). UUID used if None.")

    # --- MODIFIED VALIDATOR ---
    @model_validator(mode='after')
    def check_ayah_range(self) -> 'VideoRequest':
        """Checks if end_ayah is greater than or equal to start_ayah."""
        # 'after' mode runs after individual field validation
        # Access fields directly via self
        start = self.start_ayah
        end = self.end_ayah

        # The check for None isn't strictly necessary here because Pydantic
        # would have already raised errors if start_ayah or end_ayah were missing
        # and they are required fields (...). But it doesn't hurt.
        if start is not None and end is not None and end < start:
            # You can raise ValueError or PydanticCustomError for better FastAPI integration
            raise ValueError('end_ayah must be greater than or equal to start_ayah')
        return self # Must return the model instance (self)

# --- In-memory Job Status ---
job_status = {}

# --- Background Task Function (Updated for Multi-Ayah) ---
# ... (rest of your process_video_generation function remains the same) ...
def process_video_generation(
    request: VideoRequest,
    job_id: str
):
    """Wrapper function to run multi-ayah video generation in the background."""
    temp_audio_segment_paths: List[Path] = []
    concatenated_audio_path: Optional[Path] = None

    try:
        log.info(f"[Job {job_id}] Background task started for Surah {request.surah}, Ayahs {request.start_ayah}-{request.end_ayah}.")
        job_status[job_id] = {"status": "processing", "detail": "Fetching data for Ayahs..."}

        # --- 1. Get Reciter/Translation Info ---
        reciter_config = RECITER_INFO.get(request.reciter_key)
        translation_config = TRANSLATION_INFO.get(request.translation_key)
        if not reciter_config or not translation_config:
             raise ValueError("Invalid reciter or translation key provided internally.") # Should be caught by endpoint validation

        reciter_id_numeric = reciter_config["id"]
        translation_identifier = translation_config["identifier"]

        # --- Initialize Aggregated Data Structures ---
        all_arabic_texts: List[str] = []
        all_translation_texts: List[str] = []
        all_word_timestamps: List[Dict[str, Any]] = [] # Will contain offset timestamps
        current_audio_offset_s: float = 0.0 # Offset in seconds

        # --- 2. Loop Through Ayahs: Fetch Data, Download Audio, Calculate Offsets ---
        for ayah_index, current_ayah in enumerate(range(request.start_ayah, request.end_ayah + 1)):
            log.info(f"[Job {job_id}] Processing Ayah {request.surah}:{current_ayah} (Index {ayah_index})")
            job_status[job_id]["detail"] = f"Processing Ayah {request.surah}:{current_ayah}..."

            # --- Fetch Verse Data (Text, Timestamps, Audio URL) ---
            try:
                verse_data = fetch_quran_data_from_api(request.surah, current_ayah, reciter_id_numeric)
            except APIError as e:
                raise APIError(f"Failed to fetch data for Ayah {request.surah}:{current_ayah}: {e}")

            # --- Fetch Translation ---
            try:
                 translation_text = get_translation_text_from_api(request.surah, current_ayah, translation_identifier)
            except APIError as e:
                 raise APIError(f"Failed to fetch translation for Ayah {request.surah}:{current_ayah}: {e}")

            # --- Extract Arabic Text and Raw Timestamps ---
            arabic_text, raw_word_timestamps = get_arabic_text_and_timestamps(verse_data)
            if not arabic_text or not translation_text:
                 raise ValueError(f"Missing arabic or translation text for Ayah {request.surah}:{current_ayah}")
            # Timestamps *can* be empty if API fails, but we need audio URL regardless
            # if not raw_word_timestamps:
            #     log.warning(f"[Job {job_id}] No timestamps received for Ayah {request.surah}:{current_ayah}. Video timing might be affected.")

            # --- Extract Audio URL ---
            relative_audio_url = verse_data.get("audio", {}).get("url")
            if not relative_audio_url:
                log.error(f"[Job {job_id}] Audio URL missing for Ayah {request.surah}:{current_ayah}, reciter {reciter_id_numeric}.")
                raise ValueError(f"Failed to retrieve audio URL for Ayah {request.surah}:{current_ayah}.")
            absolute_audio_url = urljoin(QURAN_COM_AUDIO_BASE_URL, relative_audio_url)
            log.debug(f"[Job {job_id}] Ayah {current_ayah} Audio URL: {absolute_audio_url}")

            # --- Download This Ayah's Audio Segment ---
            temp_audio_file_path = download_audio_temporarily(absolute_audio_url, f"{job_id}_ayah_{current_ayah}")
            if not temp_audio_file_path:
                raise RuntimeError(f"Failed to download audio for Ayah {request.surah}:{current_ayah}.")
            temp_audio_segment_paths.append(temp_audio_file_path) # Add to list for cleanup

            # --- Calculate Duration of This Segment (for next offset) ---
            # Use the actual duration of the downloaded file
            segment_duration_s = 0.0
            try:
                # Ensure moviepy is imported if not already
                from moviepy import AudioFileClip
                with AudioFileClip(str(temp_audio_file_path)) as audio_clip:
                    segment_duration_s = audio_clip.duration
                if segment_duration_s <= 0:
                     log.warning(f"[Job {job_id}] Audio segment for Ayah {current_ayah} has zero or negative duration ({segment_duration_s:.2f}s). Offset might be incorrect.")
                     segment_duration_s = 0 # Prevent negative offsets
            except Exception as e:
                 log.error(f"[Job {job_id}] Could not read duration from temp audio {temp_audio_file_path}: {e}. Using 0 for offset.")
                 segment_duration_s = 0

            log.debug(f"[Job {job_id}] Ayah {current_ayah} audio segment duration: {segment_duration_s:.3f}s. Current total offset: {current_audio_offset_s:.3f}s")

            # --- Offset Timestamps for This Ayah and Add Ayah Index ---
            offset_timestamps_for_ayah = []
            for ts in raw_word_timestamps:
                 offset_ts = ts.copy() # Avoid modifying original dict if reused
                 # Add the *current* offset (from previous segments)
                 offset_ts['start_time'] += current_audio_offset_s
                 offset_ts['end_time'] += current_audio_offset_s
                 offset_ts['ayah_index'] = ayah_index # Add index to group timestamps later
                 offset_timestamps_for_ayah.append(offset_ts)

            # --- Append Data for this Ayah to Aggregated Lists ---
            all_arabic_texts.append(arabic_text)
            all_translation_texts.append(translation_text)
            all_word_timestamps.extend(offset_timestamps_for_ayah)

            # --- Update Offset for the *Next* Ayah ---
            current_audio_offset_s += segment_duration_s

        # --- End Ayah Loop ---

        if not all_word_timestamps:
             # This can happen if *no* ayah had timestamps, even if audio downloaded
             raise ValueError("Failed to retrieve any valid word timestamps for the requested Ayah range.")
        if not temp_audio_segment_paths:
             raise ValueError("Failed to download any audio segments for the requested Ayah range.")

        # --- 3. Concatenate Audio Segments ---
        job_status[job_id]["detail"] = "Concatenating audio..."
        log.info(f"[Job {job_id}] Starting concatenation of {len(temp_audio_segment_paths)} audio segments.")
        concatenated_audio_path = concatenate_audio_files(temp_audio_segment_paths, job_id, TEMP_DIR)

        if not concatenated_audio_path:
            raise RuntimeError("Failed to concatenate audio segments.")
        log.info(f"[Job {job_id}] Audio concatenated successfully: {concatenated_audio_path}")

        # --- Audio Segments are concatenated, original temp files can be cleaned up (done in finally) ---

        # --- 4. Determine Output Path ---
        filename_base = request.output_filename or job_id
        safe_filename_base = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in filename_base)
        # Add Ayah range to default filename
        if not request.output_filename:
             filename_base = f"S{request.surah}_A{request.start_ayah}-{request.end_ayah}_{job_id[:8]}"
             safe_filename_base = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in filename_base)

        output_file = OUTPUT_DIR / f"{safe_filename_base}.mp4"

        job_status[job_id]["detail"] = "Generating video..."
        log.info(f"[Job {job_id}] Aggregated data ready. Starting video generation process for output: {output_file}")

        # --- 5. Generate Video ---
        success = generate_quran_video(
            arabic_texts=all_arabic_texts,
            translation_texts=all_translation_texts,
            all_word_timestamps=all_word_timestamps, # Pass the combined, offset list
            concatenated_audio_path=concatenated_audio_path, # Pass the combined audio
            background_id=request.background_id,
            output_path=output_file,
            job_id=job_id
        )

        # --- 6. Update Status ---
        if success:
            job_status[job_id] = {"status": "completed", "output_path": str(output_file)}
            log.info(f"[Job {job_id}] Background task finished successfully.")
        else:
             raise RuntimeError("Video generation process failed (check generator logs).")

    except APIError as e:
         log.error(f"[Job {job_id}] API Error during processing: {e}", exc_info=False)
         job_status[job_id] = {"status": "failed", "detail": f"API Error: {e}"}
    except ValueError as e: # Catch specific value errors like missing data/URLs/range
        log.error(f"[Job {job_id}] Value Error during processing: {e}", exc_info=False)
        job_status[job_id] = {"status": "failed", "detail": f"Data/Input Error: {e}"}
    except RuntimeError as e: # Catch specific runtime errors like download/concatenation/generation failure
        log.error(f"[Job {job_id}] Runtime Error during processing: {e}", exc_info=False)
        job_status[job_id] = {"status": "failed", "detail": f"Processing Error: {e}"}
    except Exception as e:
        log.error(f"[Job {job_id}] Background task failed unexpectedly: {e}", exc_info=True)
        # Shorten traceback if it's very long for the status detail
        detail = traceback.format_exc()
        if len(detail) > 500: detail = detail[:250] + "...\n..." + detail[-250:]
        job_status[job_id] = {"status": "failed", "detail": f"Unexpected Error: {detail}"}

    finally:
        # --- Comprehensive Cleanup ---
        log.info(f"[Job {job_id}] Performing final cleanup...")
        # 1. Delete individual temporary audio segments
        for temp_path in temp_audio_segment_paths:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                    log.debug(f"[Job {job_id}] Cleaned up temporary audio segment: {temp_path}")
                except OSError as e:
                    log.error(f"[Job {job_id}] Error cleaning up segment {temp_path}: {e}")

        # 2. Delete the concatenated audio file (if it exists)
        #    This should exist if concatenation succeeded, even if video gen failed.
        if concatenated_audio_path and concatenated_audio_path.exists():
            try:
                concatenated_audio_path.unlink()
                log.info(f"[Job {job_id}] Cleaned up concatenated audio file: {concatenated_audio_path}")
            except OSError as e:
                log.error(f"[Job {job_id}] Error cleaning up concatenated audio {concatenated_audio_path}: {e}")


# --- API Endpoints ---
@app.post("/generate_video", status_code=status.HTTP_202_ACCEPTED)
async def create_video_generation_job(
    request: VideoRequest, # Uses the updated model
    background_tasks: BackgroundTasks
):
    """
    Accepts video generation parameters for a range of **consecutive Ayahs**
    and starts the process in the background using public APIs.
    Returns a job ID to track status.
    """
    # --- Input Validation (Pydantic handles range check via model_validator) ---
    if request.reciter_key not in RECITER_INFO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid reciter_key. Available: {list(RECITER_INFO.keys())}")
    if request.translation_key not in TRANSLATION_INFO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid translation_key. Available: {list(TRANSLATION_INFO.keys())}")
    if request.background_id not in BACKGROUND_MAP:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid background_id. Available: {list(BACKGROUND_MAP.keys())}")
    # Pydantic handles basic types, value ranges (surah), and start <= end check

    job_id = str(uuid.uuid4())
    log.info(f"Received multi-ayah video generation request ({request.surah}:{request.start_ayah}-{request.end_ayah}). Assigning Job ID: {job_id}")

    job_status[job_id] = {"status": "queued", "detail": "Pending execution"}
    background_tasks.add_task(process_video_generation, request, job_id)

    return {"message": "Multi-ayah video generation job accepted.", "job_id": job_id}


@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Retrieves the status of a previously submitted video generation job.
    """
    status_info = job_status.get(job_id)
    if not status_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job ID not found.")
    return {"job_id": job_id, **status_info}


@app.get("/")
async def root():
    """Provides a simple welcome message for the API root."""
    return {"message": "Welcome to the Quran Video Generator API (API-Driven). Use POST /generate_video for single or multiple Ayahs."}

# --- Run Command ---
# uvicorn main:app --reload --host 0.0.0.0 --port 8000