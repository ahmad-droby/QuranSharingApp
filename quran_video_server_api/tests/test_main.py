# tests/test_main.py
import time
import uuid
import traceback # Added for better error reporting in simulation
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY, call # Import call

import pytest
from fastapi import BackgroundTasks # Import BackgroundTasks
from fastapi.testclient import TestClient

# Assume run from project root or PYTHONPATH is set
from main import app, job_status # Import your FastAPI app and status dict
from config import TEMP_DIR, RECITER_INFO, TRANSLATION_INFO, BACKGROUND_MAP # Import config for keys
from data_loader import APIError
# Import the request model explicitly for type hints and direct use
from main import VideoRequest

client = TestClient(app)

# --- Mock Data ---
# Use valid keys directly from config if possible, otherwise define clearly
MOCK_RECITER_KEY = list(RECITER_INFO.keys())[0] if RECITER_INFO else "mishary_alafasy" # Take first available or default
MOCK_TRANSLATION_KEY = list(TRANSLATION_INFO.keys())[0] if TRANSLATION_INFO else "en_sahih"
MOCK_BACKGROUND_ID = list(BACKGROUND_MAP.keys())[0] if BACKGROUND_MAP else "nature_video"
MOCK_SURAH = 1
MOCK_AYAH = 1
# Define MOCK_JOB_ID here, but it will be overridden in tests using mocking
MOCK_JOB_ID_BASE = "test_job_base"

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
# MOCK_TEMP_AUDIO_PATH will be generated dynamically in tests based on mocked job_id


# --- Fixtures ---
@pytest.fixture(autouse=True)
def reset_job_status_and_temp():
    """Clears job status and ensures temp dir is clean before/after each test."""
    job_status.clear()
    # Clean up any leftover mock temp files from previous runs
    for item in TEMP_DIR.glob("test_job_*_mock_audio.mp3"):
        try:
            item.unlink()
        except OSError:
            pass # Ignore if file is already gone or locked
    yield # Run the test
    # Cleanup after test too, just in case
    job_status.clear() # Clear status again after test
    for item in TEMP_DIR.glob("test_job_*_mock_audio.mp3"):
        try:
            item.unlink()
        except OSError:
            pass


# --- Test Cases ---

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "API-Driven" in response.json()["message"]

# Patch the functions called *by* the background task
@patch("main.generate_quran_video", return_value=True)
@patch("main.download_audio_temporarily") # Will set return_value inside
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.get_arabic_text_and_timestamps", return_value=("بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", [{"word_index": 0, "text":"بِسْمِ","start_time":0.5, "end_time": 0.8}, {"word_index": 3, "text":"ٱلرَّحِيمِ","start_time":1.85, "end_time": 2.5}])) # Ensure timestamp list is not empty and text matches roughly
@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
@patch("fastapi.BackgroundTasks.add_task") # Mock add_task
def test_generate_video_success_flow(
    mock_add_task, # Get the mocked add_task
    mock_fetch_quran, mock_get_text_ts, mock_get_translation,
    mock_download_audio, mock_generate_video):
    """Test the happy path for job submission and simulated completion."""

    # Use a unique job_id within the test
    job_id_to_use = f"test_job_{uuid.uuid4()}"
    mock_temp_audio_path_dynamic = TEMP_DIR / f"{job_id_to_use}_mock_audio.mp3"
    mock_download_audio.return_value = mock_temp_audio_path_dynamic # Set return value dynamically

    with patch("main.uuid.uuid4", return_value=job_id_to_use): # Mock the generated job ID
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
    assert data["job_id"] == job_id_to_use # Check the mocked ID was used

    assert job_id_to_use in job_status
    assert job_status[job_id_to_use]["status"] == "queued"

    # --- Simulate background task execution ---
    mock_add_task.assert_called_once()
    call_args = mock_add_task.call_args
    target_func = call_args[0][0] # process_video_generation
    request_arg = call_args[0][1] # VideoRequest object
    job_id_arg = call_args[0][2] # job_id string

    assert target_func.__name__ == "process_video_generation"
    assert isinstance(request_arg, VideoRequest)
    assert request_arg.surah == MOCK_SURAH
    assert job_id_arg == job_id_to_use

    try:
        target_func(request_arg, job_id_arg) # Execute the background task logic synchronously
    except Exception as e:
        pytest.fail(f"Simulated background task failed unexpectedly in success flow: {e}\n{traceback.format_exc()}")
    # --- End Simulation ---

    assert job_id_to_use in job_status, "Job ID not found in status after task simulation"
    final_status = job_status[job_id_to_use]

    # Debug prints if it still fails:
    # print(f"\n--- Debug Info for test_generate_video_success_flow ---")
    # print(f"Job ID: {job_id_to_use}")
    # print(f"Final Status: {final_status}")
    # print(f"Mock generate_quran_video calls: {mock_generate_video.call_count}")
    # print(f"Mock download_audio calls: {mock_download_audio.call_count}")
    # print(f"Mock fetch_quran calls: {mock_fetch_quran.call_count}")
    # print(f"--- End Debug Info ---\n")

    assert final_status.get("status") == "completed", f"Expected status 'completed', but got '{final_status.get('status')}'"
    assert "output_path" in final_status

    # Verify mocks were called correctly *within the background task simulation*
    mock_fetch_quran.assert_called_once()
    reciter_numeric_id = RECITER_INFO[MOCK_RECITER_KEY]['id']
    mock_fetch_quran.assert_called_once_with(MOCK_SURAH, MOCK_AYAH, reciter_numeric_id)

    mock_get_translation.assert_called_once()
    translation_identifier = TRANSLATION_INFO[MOCK_TRANSLATION_KEY]['identifier']
    mock_get_translation.assert_called_once_with(MOCK_SURAH, MOCK_AYAH, translation_identifier)

    mock_download_audio.assert_called_once_with(MOCK_VERSE_DATA_SUCCESS['audio']['url'], job_id_to_use)

    mock_generate_video.assert_called_once()
    gen_args, gen_kwargs = mock_generate_video.call_args
    assert gen_kwargs.get("temp_audio_path") == mock_temp_audio_path_dynamic
    assert gen_kwargs.get("job_id") == job_id_to_use
    assert gen_kwargs.get("arabic_text") is not None # Check text was passed
    assert gen_kwargs.get("translation_text") == MOCK_TRANSLATION_SUCCESS
    assert len(gen_kwargs.get("word_timestamps", [])) > 0 # Check timestamps were passed


def test_generate_video_invalid_reciter_key():
    request_payload = {
        "surah": 1, "ayah": 1, "reciter_key": "invalid_reciter_key_xyz", # << Invalid
        "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID
    }
    response = client.post("/generate_video", json=request_payload)
    assert response.status_code == 400
    assert "Invalid reciter_key" in response.json()["detail"]

def test_generate_video_invalid_translation_key():
    request_payload = {
        "surah": 1, "ayah": 1, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": "invalid_translation_key_xyz", # << Invalid
        "background_id": MOCK_BACKGROUND_ID
    }
    response = client.post("/generate_video", json=request_payload)
    assert response.status_code == 400
    assert "Invalid translation_key" in response.json()["detail"]

def test_generate_video_invalid_background_id():
    request_payload = {
        "surah": 1, "ayah": 1, "reciter_key": MOCK_RECITER_KEY,
        "translation_key": MOCK_TRANSLATION_KEY,
        "background_id": "invalid_background_id_xyz" # << Invalid
    }
    response = client.post("/generate_video", json=request_payload)
    assert response.status_code == 400
    assert "Invalid background_id" in response.json()["detail"]


# Patch the functions called *by* the background task
@patch("main.generate_quran_video", return_value=False) # Mock video generation *failure*
@patch("main.download_audio_temporarily") # Mock dependencies needed *before* generation
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.get_arabic_text_and_timestamps", return_value=("Arabic Text", [{"word_index": 0, "text":"word","start_time":0.5, "end_time": 2.5}]))
@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
@patch("fastapi.BackgroundTasks.add_task")
def test_generate_video_generation_step_failure(
    mock_add_task, # Get the mocked add_task
    mock_fetch_quran, mock_get_text_ts, mock_get_translation,
    mock_download_audio, mock_generate_video):
    """Test when the video generation itself fails."""

    job_id_to_use = f"test_job_{uuid.uuid4()}" # Unique job ID
    mock_temp_audio_path_dynamic = TEMP_DIR / f"{job_id_to_use}_mock_audio.mp3"
    mock_download_audio.return_value = mock_temp_audio_path_dynamic # Set return value

    # Explicitly reset mock count before simulation for this specific test
    mock_generate_video.reset_mock()

    with patch("main.uuid.uuid4", return_value=job_id_to_use):
        request_payload = {
            "surah": MOCK_SURAH,
            "ayah": MOCK_AYAH,
            "reciter_key": MOCK_RECITER_KEY,
            "translation_key": MOCK_TRANSLATION_KEY,
            "background_id": MOCK_BACKGROUND_ID,
        }
        response = client.post("/generate_video", json=request_payload)

    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert job_id == job_id_to_use

    # --- Simulate background task execution ---
    mock_add_task.assert_called_once()
    call_args = mock_add_task.call_args
    target_func, request_arg, job_id_arg = call_args[0]
    assert job_id_arg == job_id_to_use

    try:
        target_func(request_arg, job_id_arg) # Execute the background task logic
    except Exception as e:
         pytest.fail(f"Simulated background task failed unexpectedly in generation failure test: {e}\n{traceback.format_exc()}")
    # --- End Simulation ---

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    # Check detail message - should contain the RuntimeError text from main.py
    assert "Video generation process failed" in final_status["detail"]

    # Crucially, check generate_quran_video was called ONCE during this test's simulation
    mock_generate_video.assert_called_once()


@patch("main.fetch_quran_data_from_api", side_effect=APIError("Quran.com API Down"))
@patch("fastapi.BackgroundTasks.add_task") # Mock add_task here too
def test_generate_video_api_fetch_failure(mock_add_task, mock_fetch_quran):
    job_id_to_use = f"test_job_{uuid.uuid4()}"
    with patch("main.uuid.uuid4", return_value=job_id_to_use):
        request_payload = {
            "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
            "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
        }
        response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]
    assert job_id == job_id_to_use

    # Simulate background run
    mock_add_task.assert_called_once()
    call_args = mock_add_task.call_args
    target_func, request_arg, job_id_arg = call_args[0]
    assert job_id_arg == job_id_to_use

    try:
        target_func(request_arg, job_id_arg) # Execute the task
    except Exception as e:
         pytest.fail(f"Simulated background task failed unexpectedly in API fetch failure test: {e}\n{traceback.format_exc()}")

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    assert "API Error: Quran.com API Down" in final_status["detail"]
    # Ensure fetch_quran was called once before it failed
    mock_fetch_quran.assert_called_once()


@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS) # Step 1 OK
@patch("main.get_translation_text_from_api", side_effect=APIError("AlQuran.Cloud API Down")) # Step 2 Fail
@patch("fastapi.BackgroundTasks.add_task") # Mock add_task
def test_generate_video_api_translation_failure(mock_add_task, mock_get_translation, mock_fetch_quran):
    job_id_to_use = f"test_job_{uuid.uuid4()}"
    with patch("main.uuid.uuid4", return_value=job_id_to_use):
        request_payload = {
            "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
            "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
        }
        response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]
    assert job_id == job_id_to_use

    # Simulate background run
    mock_add_task.assert_called_once()
    call_args = mock_add_task.call_args
    target_func, request_arg, job_id_arg = call_args[0]
    assert job_id_arg == job_id_to_use

    try:
        target_func(request_arg, job_id_arg) # Execute the task
    except Exception as e:
        pytest.fail(f"Simulated background task failed unexpectedly in translation failure test: {e}\n{traceback.format_exc()}")

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    assert "API Error: AlQuran.Cloud API Down" in final_status["detail"]
    mock_fetch_quran.assert_called_once() # Ensure fetch was called
    mock_get_translation.assert_called_once() # Ensure translation attempt was made


@patch("main.fetch_quran_data_from_api", return_value=MOCK_VERSE_DATA_SUCCESS)
@patch("main.get_arabic_text_and_timestamps", return_value=("Arabic Text", [{"start_time":0.5, "end_time": 2.5}]))
@patch("main.get_translation_text_from_api", return_value=MOCK_TRANSLATION_SUCCESS)
@patch("main.download_audio_temporarily", return_value=None) # << Audio Download Fails
@patch("fastapi.BackgroundTasks.add_task")
def test_generate_video_audio_download_failure(mock_add_task, mock_download_audio, mock_get_translation, mock_get_text_ts, mock_fetch_quran):
    job_id_to_use = f"test_job_{uuid.uuid4()}"
    with patch("main.uuid.uuid4", return_value=job_id_to_use):
        request_payload = {
            "surah": MOCK_SURAH, "ayah": MOCK_AYAH, "reciter_key": MOCK_RECITER_KEY,
            "translation_key": MOCK_TRANSLATION_KEY, "background_id": MOCK_BACKGROUND_ID,
        }
        response = client.post("/generate_video", json=request_payload)
    job_id = response.json()["job_id"]
    assert job_id == job_id_to_use

    # Simulate background run
    mock_add_task.assert_called_once()
    call_args = mock_add_task.call_args
    target_func, request_arg, job_id_arg = call_args[0]
    assert job_id_arg == job_id_to_use

    try:
        target_func(request_arg, job_id_arg) # Execute the task
    except Exception as e:
        pytest.fail(f"Simulated background task failed unexpectedly in download failure test: {e}\n{traceback.format_exc()}")

    assert job_id in job_status
    final_status = job_status[job_id]
    assert final_status["status"] == "failed"
    # Check detail message from main.py when download returns None
    assert "Failed to download audio file" in final_status["detail"]
    mock_fetch_quran.assert_called_once()
    mock_get_translation.assert_called_once()
    mock_download_audio.assert_called_once() # Ensure download was attempted


# --- Status Check Tests ---

def test_get_job_status_not_found():
    response = client.get("/jobs/non_existent_job_id_12345/status")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job ID not found."

def test_get_job_status_found_processing():
    job_id = f"test_status_job_{uuid.uuid4()}"
    job_status[job_id] = {"status": "processing", "detail": "Fetching data..."}
    response = client.get(f"/jobs/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "processing"
    assert data["detail"] == "Fetching data..."

def test_get_job_status_found_completed():
    job_id = f"test_status_job_{uuid.uuid4()}"
    output_file_path = str(Path("output") / f"{job_id}.mp4")
    job_status[job_id] = {"status": "completed", "output_path": output_file_path}
    response = client.get(f"/jobs/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["output_path"] == output_file_path

def test_get_job_status_found_failed():
    job_id = f"test_status_job_{uuid.uuid4()}"
    job_status[job_id] = {"status": "failed", "detail": "API Error: Something went wrong."}
    response = client.get(f"/jobs/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "failed"
    assert data["detail"] == "API Error: Something went wrong."