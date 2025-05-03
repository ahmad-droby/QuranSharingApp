# tests/test_main.py
import time
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import pytest
from fastapi.testclient import TestClient

# Assume run from project root or PYTHONPATH is set
from main import app, job_status # Import your FastAPI app and status dict
from config import TEMP_DIR # For checking cleanup potentially
from data_loader import APIError

client = TestClient(app)

# --- Mock Data ---
MOCK_RECITER_KEY = "mishary_alafasy"
MOCK_TRANSLATION_KEY = "en_sahih"
MOCK_BACKGROUND_ID = "nature_video"
MOCK_SURAH = 1
MOCK_AYAH = 1
MOCK_JOB_ID = str(uuid.uuid4())

MOCK_VERSE_DATA_SUCCESS = {
    "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
    "words": [
        {"text_uthmani": "بِسْمِ", "timestamp_from": 500, "timestamp_to": 800},
        {"text_uthmani": "ٱللَّهِ", "timestamp_from": 810, "timestamp_to": 1100},
        {"text_uthmani": "ٱلرَّحْمَٰنِ", "timestamp_from": 1150, "timestamp_to": 1800},
        {"text_uthmani": "ٱلرَّحِيمِ", "timestamp_from": 1850, "timestamp_to": 2500}
    ],
    "audio": {"url": "http://fake.audio/url/001_001.mp3"}
}
MOCK_TRANSLATION_SUCCESS = "In the name of Allah, the Entirely Merciful, the Especially Merciful."
MOCK_TEMP_AUDIO_PATH = TEMP_DIR / f"{MOCK_JOB_ID}_mock_audio.mp3"


# --- Fixtures ---
@pytest.fixture(autouse=True)
def reset_job_status_and_temp():
    """Clears job status and ensures temp dir is clean before each test."""
    job_status.clear()
    # Clean up any leftover mock temp files
    for item in TEMP_DIR.glob(f"{MOCK_JOB_ID}_*"):
        item.unlink()
    yield # Run the test
    # Cleanup after test too, just in case
    for item in TEMP_DIR.glob(f"{MOCK_JOB_ID}_*"):
        item.unlink()


# --- Helper ---
def run_background_tasks(test_client):
     """ Placeholder to simulate background task execution if TestClient supported it easily.
         For now, we mock the target function directly. """
     # In a more complex setup (e.g., with lifespan events), you might trigger task runners here.
     pass

# --- Test Cases ---

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "API-Driven" in response.json()["message"]

# Patch the functions called by the background task
@patch("main.generate_quran_video", return_value=True) # Mock video generation success
@patch("main.download_audio_temporarily", return_value=MOCK_TEMP_AUDIO_PATH)
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.get_arabic_text_and_timestamps", return_value=("Arabic Text", [{"start_time":0.5, "end_time": 2.5}]))
@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
def test_generate_video_success_flow(
    mock_fetch_quran, mock_get_text_ts, mock_get_translation,
    mock_download_audio, mock_generate_video):
    """Test the happy path for job submission and simulated completion."""

    request_payload = {
        "surah": MOCK_SURAH,
        "ayah": MOCK_AYAH,
        "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY,
        "background_id": MOCK_BACKGROUND_ID,
    }
    response = client.post("/generate_video", json=request_payload)

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    assert job_id in job_status
    assert job_status[job_id]["status"] == "queued"

    # --- Simulate background task execution ---
    # Since TestClient doesn't run them, we manually call the patched function's logic
    # (or ideally, mock the BackgroundTasks.add_task call itself to capture args)
    # Here, we'll just call the core logic function directly for simplicity,
    # assuming add_task placed it correctly.
    from main import process_video_generation
    from main import VideoRequest # Need the model

    # Re-create the request object as the background task would receive it
    video_request_obj = VideoRequest(**request_payload)

    # Run the task logic synchronously
    process_video_generation(video_request_obj, job_id)
    # --- End Simulation ---

    # Now check the final status
    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "completed"
    assert "output_path" in final_status

    # Verify mocks were called
    mock_fetch_quran.assert_called_once()
    mock_get_translation.assert_called_once()
    mock_download_audio.assert_called_once()
    mock_generate_video.assert_called_once()
    # Check if the temp audio path was passed correctly to generation
    args, kwargs = mock_generate_video.call_args
    assert kwargs.get("temp_audio_path") == MOCK_TEMP_AUDIO_PATH


def test_generate_video_invalid_reciter_key():
    request_payload = {
        "surah": 1, "ayah": 1, "reciter_key": "invalid_reciter", # << Invalid
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID
    }
    response = client.post("/generate_video", json=request_payload)
    assert response.status_code == 400
    assert "Invalid reciter_key" in response.json()["detail"]

# --- Test API Failure Scenarios ---

@patch("main.fetch_quran_data_from_api", side_effect=APIError("Quran.com Down"))
def test_generate_video_api_fetch_failure(mock_fetch_quran):
    request_payload = {
        "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
    }
    response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]

    # Simulate background run
    from main import process_video_generation, VideoRequest
    video_request_obj = VideoRequest(**request_payload)
    process_video_generation(video_request_obj, job_id)

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    assert "API Error: Quran.com Down" in final_status["detail"]

@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS) # Step 1 OK
@patch("main.get_translation_text_from_api", side_effect=APIError("AlQuran.Cloud Down")) # Step 2 Fail
def test_generate_video_api_translation_failure(mock_get_translation, mock_fetch_quran):
    request_payload = {
        "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
    }
    response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]

    # Simulate background run
    from main import process_video_generation, VideoRequest
    video_request_obj = VideoRequest(**request_payload)
    process_video_generation(video_request_obj, job_id)

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    assert "API Error: AlQuran.Cloud Down" in final_status["detail"]


@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.download_audio_temporarily", return_value=None) # << Audio Download Fails
def test_generate_video_audio_download_failure(mock_download_audio, mock_get_translation, mock_fetch_quran):
    request_payload = {
        "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
    }
    response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]

    # Simulate background run
    from main import process_video_generation, VideoRequest
    video_request_obj = VideoRequest(**request_payload)
    process_video_generation(video_request_obj, job_id)

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    # Check detail message (might vary slightly based on error handling)
    assert "Failed to download audio file" in final_status["detail"]


@patch("main.generate_quran_video", return_value=False) # Mock video generation *failure*
@patch("main.download_audio_temporarily", return_value=MOCK_TEMP_AUDIO_PATH)
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.get_arabic_text_and_timestamps", return_value=("Arabic Text", [{"start_time":0.5, "end_time": 2.5}]))
@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
def test_generate_video_generation_step_failure(
    mock_fetch_quran, mock_get_text_ts, mock_get_translation,
    mock_download_audio, mock_generate_video):
    """Test when the video generation itself fails."""
    request_payload = {
        "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
    }
    response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]

    # Simulate background run
    from main import process_video_generation, VideoRequest
    video_request_obj = VideoRequest(**request_payload)
    process_video_generation(video_request_obj, job_id)

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    assert "Video generation process failed" in final_status["detail"]
    mock_generate_video.assert_called_once() # Ensure it was called


def test_get_job_status_not_found():
    response = client.get("/jobs/non_existent_job_id/status")
    assert response.status_code == 404

def test_get_job_status_found():
    job_id = "test_status_job"
    job_status[job_id] = {"status": "processing", "detail": "Fetching..."}
    response = client.get(f"/jobs/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "processing"