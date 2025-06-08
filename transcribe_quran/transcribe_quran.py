# transcribe_quran.py
import argparse
import asyncio
import json
import logging
import difflib
import unicodedata
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

from transformers import WhisperProcessor, WhisperForConditionalGeneration, GenerationConfig, pipeline as hf_pipeline
from peft import PeftModel
import torch
import librosa
from moviepy import VideoFileClip

from config import (
    TEMP_DIR, OUTPUT_DIR, TRANSLATION_INFO, TAFSEER_INFO, SURAH_AYAHS_COUNT
)
from data_loader import (
    get_quran_ayah_ground_truth, get_translation_text_cached, get_tafseer_text_cached,
    get_ayah_text_and_words_from_cache_sync
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("transformers").setLevel(logging.WARNING)
log = logging.getLogger("transcribe_quran_cli")

# === Proportional Timestamp Distribution Helper ===
def distribute_time_proportionally(words_list: List[Dict], start_time: float, end_time: float) -> List[Dict]:
    """Distributes a time range proportionally over words based on their character length."""
    if not words_list: return []
    total_chars = sum(len(w.get('text', '')) for w in words_list)
    if total_chars == 0: return [{**w, 'start_time': start_time, 'end_time': end_time} for w in words_list]

    duration_per_char = (end_time - start_time) / total_chars
    current_time = start_time
    for word in words_list:
        word_len = len(word.get('text', ''))
        word_duration = word_len * duration_per_char
        word['start_time'] = current_time
        word['end_time'] = current_time + word_duration
        current_time += word_duration
    return words_list


# --- Text Normalization ---
def normalize_arabic_for_matching(text: str) -> str:
    if not text: return ""
    text = unicodedata.normalize('NFKD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub("[أإآٱ]", "ا", text)
    text = re.sub("[ؤ]", "و", text)
    text = re.sub("[ى]", "ي", text)
    text = re.sub("ة", "ه", text)
    text = text.replace('ـ', '')
    text = " ".join(text.split())
    return text.lower()

# --- Auto-Detection Logic ---
def find_best_quran_segment_match(
    asr_text_normalized: str,
    min_match_ratio: float = 0.4, # Lowered for better auto-detection
    surah_hint: Optional[int] = None
) -> Optional[Tuple[int, int, int, float]]:
    log.info(f"Auto-detect: Scanning ASR (len {len(asr_text_normalized)} chars). Min ratio: {min_match_ratio}, Surah Hint: {surah_hint}")
    if not asr_text_normalized.strip() or len(asr_text_normalized.split()) < 2:
        log.warning("Auto-detect: ASR text too short or empty.")
        return None

    best_overall_match: Optional[Tuple[int, int, int, float]] = None
    surahs_to_scan = [surah_hint] if surah_hint and 1 <= surah_hint <= 114 else range(1, 114 + 1)

    for surah_num in surahs_to_scan:
        ayah_count_in_surah = SURAH_AYAHS_COUNT[surah_num]
        concatenated_surah_gt_norm = ""
        ayah_char_boundaries: Dict[int, Tuple[int, int]] = {}
        current_char_pos = 0
        surah_has_text = False

        for ayah_num_in_surah in range(1, ayah_count_in_surah + 1):
            ayah_data = get_ayah_text_and_words_from_cache_sync(surah_num, ayah_num_in_surah)
            if ayah_data and ayah_data.get("text_uthmani") and ayah_data.get("text_uthmani") != "Error":
                norm_text = normalize_arabic_for_matching(ayah_data["text_uthmani"]) + " "
                concatenated_surah_gt_norm += norm_text
                ayah_char_boundaries[ayah_num_in_surah] = (current_char_pos, current_char_pos + len(norm_text) - 1)
                current_char_pos += len(norm_text)
                surah_has_text = True
        
        if not surah_has_text or not concatenated_surah_gt_norm.strip(): continue

        s = difflib.SequenceMatcher(None, asr_text_normalized, concatenated_surah_gt_norm, autojunk=False)
        match = s.find_longest_match(0, len(asr_text_normalized), 0, len(concatenated_surah_gt_norm))

        if match.size > 0:
            asr_matched_segment = asr_text_normalized[match.a : match.a + match.size]
            gt_matched_segment = concatenated_surah_gt_norm[match.b : match.b + match.size]
            current_segment_ratio = difflib.SequenceMatcher(None, asr_matched_segment, gt_matched_segment).ratio()

            if current_segment_ratio >= min_match_ratio:
                start_ayah_detected, end_ayah_detected = -1, -1
                for ay_n, (s_char, e_char) in ayah_char_boundaries.items():
                    if s_char <= match.b <= e_char: start_ayah_detected = ay_n; break
                if start_ayah_detected == -1 and ayah_char_boundaries:
                    for ay_n_rev, (s_char_rev, _) in sorted(ayah_char_boundaries.items(), key=lambda x: x[0], reverse=True):
                        if s_char_rev <= match.b: start_ayah_detected = ay_n_rev; break
                    if start_ayah_detected == -1 : start_ayah_detected = min(ayah_char_boundaries.keys())

                match_end_char_idx = match.b + match.size - 1
                for ay_n, (s_char, e_char) in sorted(ayah_char_boundaries.items(), reverse=True):
                    if s_char <= match_end_char_idx <= e_char: end_ayah_detected = ay_n; break
                if end_ayah_detected == -1 and ayah_char_boundaries:
                     for ay_n_fwd, (_, e_char_fwd) in ayah_char_boundaries.items():
                         if e_char_fwd >= match_end_char_idx: end_ayah_detected = ay_n_fwd; break
                     if end_ayah_detected == -1: end_ayah_detected = max(ayah_char_boundaries.keys())
                
                if start_ayah_detected != -1 and end_ayah_detected != -1:
                    if start_ayah_detected > end_ayah_detected :
                        start_ayah_detected, end_ayah_detected = end_ayah_detected, start_ayah_detected 

                    if best_overall_match is None or current_segment_ratio > best_overall_match[3]:
                        best_overall_match = (surah_num, start_ayah_detected, end_ayah_detected, current_segment_ratio)
                        log.info(f"Auto-detect: New best: S{surah_num}:A{start_ayah_detected}-{end_ayah_detected}, R:{current_segment_ratio:.3f}")
    if best_overall_match:
        log.info(f"Auto-detect: Final best: S{best_overall_match[0]}:A{best_overall_match[1]}-{best_overall_match[2]}, R:{best_overall_match[3]:.4f}")
    else:
        log.warning(f"Auto-detect: No segment found meeting min_match_ratio {min_match_ratio} with hint {surah_hint}.")
    return best_overall_match

# --- Main Processing Function ---
async def generate_timestamps_for_media(
    media_path: Path,
    output_path: Path,
    surah_hint: Optional[int],
    start_ayah_hint: Optional[int],
    end_ayah_hint: Optional[int],
    translation_key: Optional[str],
    tafseer_key: Optional[str],
    min_match_ratio: float = 0.4, # Lowered for better auto-detection
    base_model_id: str = "openai/whisper-large-v2", # Changed to a more general Whisper model for timestamps
    lora_model_id: Optional[str] = None, # Disabling LoRA as it might not be compatible with large-v2
    force_cache_refresh: bool = False,
    use_gpu_if_available: bool = True,
    hf_token: Optional[str] = None,
    pipeline_batch_size: int = 8,
    pipeline_chunk_length_s: int = 30
):
    log.info(f"Processing media file: {media_path} with base model {base_model_id} and LoRA {lora_model_id if lora_model_id else 'None'}")
    processing_errors: List[str] = []
    temp_audio_file: Optional[Path] = None
    audio_input_np: Optional[Any] = None

    # 1. Prepare Audio File
    if media_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']:
        try:
            log.info("Video file provided, extracting audio...")
            video = VideoFileClip(str(media_path))
            temp_audio_file = TEMP_DIR / f"{media_path.stem}_{Path(media_path).stat().st_mtime_ns}_extracted_audio.mp3"
            video.audio.write_audiofile(str(temp_audio_file), codec='libmp3lame', logger=None)
            audio_to_process_path = temp_audio_file
            log.info(f"Audio extracted to: {temp_audio_file}")
            video.close()
        except Exception as e:
            log.error(f"Failed to extract audio from video: {e}", exc_info=True)
            processing_errors.append(f"Audio extraction failed: {e}")
            final_result = {"error": "Audio extraction failed.", "details": processing_errors}
            with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_result, f, indent=2, ensure_ascii=False)
            return
    elif media_path.suffix.lower() in ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']:
        audio_to_process_path = media_path
    else:
        log.error(f"Unsupported file type: {media_path.suffix}")
        processing_errors.append(f"Unsupported file type: {media_path.suffix}")
        final_result = {"error": "Unsupported file type.", "details": processing_errors}
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_result, f, indent=2, ensure_ascii=False)
        return

    try:
        log.info(f"Loading and resampling audio from: {audio_to_process_path.name}")
        audio_input_np, _ = librosa.load(str(audio_to_process_path), sr=16000, mono=True, dtype='float32')
        log.info(f"Audio loaded. Duration: {len(audio_input_np)/16000.0:.2f}s, Shape: {audio_input_np.shape}")
    except Exception as e:
        log.error(f"Failed to load or resample audio using librosa: {e}", exc_info=True)
        processing_errors.append(f"Audio loading/resampling failed: {e}")
        final_result = {"error": "Audio loading/resampling failed.", "details": processing_errors}
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_result, f, indent=2, ensure_ascii=False)
        if temp_audio_file and temp_audio_file.exists(): temp_audio_file.unlink(missing_ok=True)
        return
 

    # 2. Transcribe Audio using Hugging Face Pipeline
    asr_segments_with_ts: List[Dict] = []
    full_asr_text = ""
    
    device_str = "cpu"
    if use_gpu_if_available and torch.cuda.is_available():
        device_str = "cuda"
    elif use_gpu_if_available and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device_str = "mps"
    log.info(f"Using device: {device_str} for ASR.")
    dtype = torch.float16 if device_str != "cpu" else torch.float32 

    loaded_model = None
    loaded_processor = None
    try:
        log.info(f"Loading base ASR model components: {base_model_id}")
        loaded_processor = WhisperProcessor.from_pretrained(base_model_id, token=hf_token)
        
        base_whisper_model = WhisperForConditionalGeneration.from_pretrained(
            base_model_id, torch_dtype=dtype, token=hf_token,
        ).to(device_str)

        if lora_model_id:
            log.info(f"Applying LoRA adapter: {lora_model_id}")
            loaded_model = PeftModel.from_pretrained(base_whisper_model, lora_model_id, token=hf_token)
            log.info("LoRA adapter applied successfully.")
        else:
            loaded_model = base_whisper_model
        
        loaded_model.eval()
        log.info(f"Model loaded on device: {loaded_model.device}")

        log.info("Initializing ASR pipeline...")
        
        # --- Prepare GenerationConfig for the Pipeline ---
        # Start with the model's default generation config
        base_model_for_config = loaded_model
        if hasattr(loaded_model, 'get_base_model'): # PEFT >= 0.7.0
            base_model_for_config = loaded_model.get_base_model()
        elif hasattr(loaded_model, 'base_model') and hasattr(loaded_model.base_model, 'model'): # Older PEFT
             base_model_for_config = loaded_model.base_model.model
        elif hasattr(loaded_model, 'model') and isinstance(loaded_model.model, WhisperForConditionalGeneration): # Other wrapping
             base_model_for_config = loaded_model.model
        # Else, loaded_model itself is the base model (no PEFT or simple wrapper)

        if hasattr(base_model_for_config, 'generation_config') and base_model_for_config.generation_config is not None:
            pipeline_gen_config = base_model_for_config.generation_config
            log.info("Cloned generation_config from model for pipeline.")
        else:
            log.warning("Model had no generation_config, creating one from model's main config for pipeline.")
            pipeline_gen_config = GenerationConfig.from_model_config(base_model_for_config.config)

        # Configure for timestamp generation
        try:
            # Get token IDs for decoder prompts
            decoder_prompt_ids_for_pipeline = loaded_processor.get_decoder_prompt_ids(
                language="ar",
                task="transcribe",
                no_timestamps=False  # IMPORTANT: Allow timestamps
            )
            
            # Set required timestamp generation parameters
            pipeline_gen_config.forced_decoder_ids = decoder_prompt_ids_for_pipeline
            pipeline_gen_config.return_timestamps = True
            if hasattr(loaded_processor.tokenizer, 'no_timestamps_token_id'):
                pipeline_gen_config.no_timestamps_token_id = loaded_processor.tokenizer.no_timestamps_token_id
            else:
                # Fallback: Try to find the no_timestamps token ID in the tokenizer
                try:
                    pipeline_gen_config.no_timestamps_token_id = loaded_processor.tokenizer.convert_tokens_to_ids(["<|notimestamps|>"])[0]
                except:
                    pipeline_gen_config.no_timestamps_token_id = loaded_processor.tokenizer.convert_tokens_to_ids(["<|nospeech|>"])[0]
            
            log.info(f"Configured GenerationConfig for timestamps: forced_decoder_ids={decoder_prompt_ids_for_pipeline}, no_timestamps_token_id={pipeline_gen_config.no_timestamps_token_id}")
        except Exception as e_fdi_pipe:
            log.error(f"Failed to set forced_decoder_ids for pipeline: {e_fdi_pipe}. Timestamps might fail.", exc_info=True)
            processing_errors.append(f"Failed to set forced_decoder_ids for pipeline: {e_fdi_pipe}")
        
        # Ensure language/task are not set as attributes if forced_decoder_ids is used
        if hasattr(pipeline_gen_config, 'language'): delattr(pipeline_gen_config, 'language')
        if hasattr(pipeline_gen_config, 'task'): delattr(pipeline_gen_config, 'task')
        pipeline_gen_config.max_new_tokens = 440 # Ensure max_new_tokens is reasonable per chunk

        log.info(f"Final GenerationConfig for pipeline: {pipeline_gen_config}")

        # Validate no_timestamps_token_id is set
        if not hasattr(pipeline_gen_config, 'no_timestamps_token_id') or pipeline_gen_config.no_timestamps_token_id is None:
            log.error("no_timestamps_token_id not properly configured in GenerationConfig")
            processing_errors.append("ASR pipeline configuration error: no_timestamps_token_id missing")
            raise ValueError("no_timestamps_token_id must be set for timestamp generation")

        # Create pipeline with full GenerationConfig
        asr_pipeline = hf_pipeline(
            task="automatic-speech-recognition",
            model=loaded_model,
            tokenizer=loaded_processor.tokenizer,
            feature_extractor=loaded_processor.feature_extractor,
            device=loaded_model.device,
            chunk_length_s=pipeline_chunk_length_s,
            batch_size=pipeline_batch_size,
            generate_kwargs={"generation_config": pipeline_gen_config} # Pass the full config object via generate_kwargs
        )
        
        log.info(f"Transcribing audio with pipeline (chunk_length_s={pipeline_chunk_length_s}, batch_size={pipeline_batch_size})...")
        pipeline_output = asr_pipeline(audio_input_np.copy())
        log.debug(f"Raw pipeline output: {pipeline_output}") # Add this line to inspect the output
        
        full_asr_text = pipeline_output.get("text", "").strip()
        log.info(f"ASR Full Text (from pipeline): {full_asr_text[:200]}...")
        
        if "chunks" in pipeline_output:
            for chunk_data in pipeline_output["chunks"]:
                asr_segments_with_ts.append({
                    "text": str(chunk_data.get("text", "")).strip(),
                    "start": chunk_data["timestamp"][0],
                    "end": chunk_data["timestamp"][1],
                    "confidence": None
                })
            log.info(f"Pipeline extracted {len(asr_segments_with_ts)} timestamped words.")
        else:
            log.warning("Pipeline did not return 'chunks' for word timestamps. Word-level timing will be unavailable.")
            processing_errors.append("Pipeline failed to provide word timestamps.")

        if not full_asr_text and asr_segments_with_ts:
            full_asr_text = " ".join(c["text"] for c in asr_segments_with_ts if c["text"].strip()).strip()
            log.info(f"Reconstructed ASR text from pipeline chunks: {full_asr_text[:200]}...")
        
        if not full_asr_text:
            processing_errors.append("ASR (pipeline) produced no text.")

    except Exception as e:
        log.error(f"ASR pipeline processing failed: {e}", exc_info=True)
        processing_errors.append(f"ASR pipeline critical error: {e}")
    finally:
        if loaded_model is not None: del loaded_model
        if loaded_processor is not None: del loaded_processor
        if device_str == "cuda": torch.cuda.empty_cache()
        elif device_str == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()
        log.info("Cleaned up ASR model and processor from memory (if loaded).")
    
    # 3. Determine Quranic Range
    final_surah, final_start_ayah, final_end_ayah = surah_hint, start_ayah_hint, end_ayah_hint
    if not (final_surah and final_start_ayah and final_end_ayah):
        if full_asr_text:
            normalized_asr = normalize_arabic_for_matching(full_asr_text)
            if normalized_asr.strip():
                log.info("No complete hints provided. Attempting auto-detection.")
                match_info = find_best_quran_segment_match(normalized_asr, min_match_ratio, surah_hint)
                if match_info:
                    final_surah, final_start_ayah, final_end_ayah, ratio = match_info
                    detection_msg = f"Auto-detected range: S{final_surah}:A{final_start_ayah}-{final_end_ayah} (Ratio:{ratio:.3f})."
                    log.info(detection_msg); processing_errors.append(detection_msg)
                else:
                    processing_errors.append(f"Auto-detection failed (min_ratio:{min_match_ratio}). Range undetermined.")
            else: processing_errors.append("ASR output empty after normalization; auto-detection skipped.")
        else: processing_errors.append("No ASR output and no range hints; cannot determine range.")
    else:
        log.info(f"Using provided hints: S{final_surah}:A{final_start_ayah}-{final_end_ayah}")

    if not (final_surah and final_start_ayah and final_end_ayah):
        log.error("Could not determine Quranic range for processing.")
        processing_errors.append("Quranic range could not be determined.")
        final_result = {
            "error": "Could not determine Quranic range.",
            "full_transcription_from_asr": full_asr_text,
            "asr_segments_with_ts_raw": asr_segments_with_ts, # Renamed key for clarity
            "details": processing_errors
        }
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_result, f, indent=2, ensure_ascii=False)
        if temp_audio_file and temp_audio_file.exists(): temp_audio_file.unlink(missing_ok=True)
        return

    log.info(f"Final processing range: S{final_surah}:A{final_start_ayah}-{final_end_ayah}")

    # 4. Fetch Ground Truth, Align, and Add Extras
    result_ayah_data: List[Dict[str, Any]] = []
    all_quran_gt_words_structured: List[Dict] = []
    current_gt_word_global_idx = 0

    for ayah_num in range(final_start_ayah, final_end_ayah + 1):
        ayah_item: Dict[str, Any] = {"surah": final_surah, "ayah_number": ayah_num, "word_timestamps": []}
        quran_data = await get_quran_ayah_ground_truth(final_surah, ayah_num, force_api=force_cache_refresh)
        
        if quran_data and quran_data.get("text_uthmani") and quran_data.get("text_uthmani") != "Error":
            ayah_item["arabic_text_ground_truth"] = quran_data["text_uthmani"]
            for idx, word_obj in enumerate(quran_data.get("words", [])):
                all_quran_gt_words_structured.append({
                    "text": word_obj["text_uthmani"], "surah_num": final_surah, "ayah_num": ayah_num,
                    "word_idx_in_ayah": idx, "global_idx": current_gt_word_global_idx,
                    "char_offset_start": word_obj["char_offset_start"], "char_offset_end": word_obj["char_offset_end"]
                })
                current_gt_word_global_idx += 1
        else:
            ayah_item["arabic_text_ground_truth"] = "Error: Text unavailable"
            processing_errors.append(f"GT text load failed for S{final_surah}:A{ayah_num}.")
        
        if translation_key:
            ayah_item["translation_key"] = translation_key
            trans_text = await get_translation_text_cached(final_surah, ayah_num, translation_key, force_api=force_cache_refresh)
            ayah_item["translation_text"] = trans_text if trans_text is not None else "Translation not available."
        
        if tafseer_key:
            ayah_item["tafseer_key"] = tafseer_key
            taf_text = await get_tafseer_text_cached(final_surah, ayah_num, tafseer_key, force_api=force_cache_refresh)
            ayah_item["tafseer_text"] = taf_text if taf_text is not None else "Tafseer not available."
            
        result_ayah_data.append(ayah_item)

    # This is the main ASR text and its segment timestamp
    # Assuming only one chunk with full audio transcription and its duration
    main_asr_segment_text = ""
    main_asr_segment_start = 0.0
    main_asr_segment_end = 0.0

    if asr_segments_with_ts:
        # Take the first (and usually only) ASR segment for full audio timing
        main_asr_segment_text = asr_segments_with_ts[0].get("text", "")
        main_asr_segment_start = asr_segments_with_ts[0].get("start", 0.0)
        main_asr_segment_end = asr_segments_with_ts[0].get("end", 0.0)
        log.info(f"Main ASR segment: '{main_asr_segment_text[:50]}...' [{main_asr_segment_start:.2f}-{main_asr_segment_end:.2f}]")
    else:
        log.warning("No ASR segments with timestamps available to distribute.")
        processing_errors.append("No ASR segment timestamps available for distribution.")


    # Reset the gt_global_idx_to_asr_idx_map logic, as we are now doing proportional distribution
    # The previous alignment logic was for direct word-to-word mapping, which is not happening.
    
    # Iterate through ayahs and distribute timestamps to their words
    current_segment_text_normalized = normalize_arabic_for_matching(main_asr_segment_text)
    current_segment_char_idx = 0 # To track position in the main ASR segment

    for ayah_obj_dict in result_ayah_data:
        gt_words_for_this_ayah = [
            w for w in all_quran_gt_words_structured
            if w["surah_num"] == ayah_obj_dict["surah"] and w["ayah_num"] == ayah_obj_dict["ayah_number"]
        ]
        
        # Concatenate normalized GT words for sequence matching
        ayah_gt_normalized_text = " ".join([normalize_arabic_for_matching(w["text"]) for w in gt_words_for_this_ayah])

        # Find where this ayah's GT text matches in the overall ASR segment text
        s = difflib.SequenceMatcher(None, current_segment_text_normalized, ayah_gt_normalized_text, autojunk=False)
        match = s.find_longest_match(0, len(current_segment_text_normalized), 0, len(ayah_gt_normalized_text))

        ayah_match_start_char = current_segment_char_idx # Default start of match for this ayah from overall segment
        ayah_match_end_char = current_segment_char_idx + len(ayah_gt_normalized_text) # Default end of match

        # Calculate the ratio of the matched segment to the current ayah's GT text
        # If the match size is very small compared to the ayah text, it's not a good match
        match_ratio = 0.0
        if ayah_gt_normalized_text and match.size > 0:
            s_match_segment = difflib.SequenceMatcher(None, current_segment_text_normalized[match.a : match.a + match.size], ayah_gt_normalized_text[match.b : match.b + match.size])
            match_ratio = s_match_segment.ratio()

        if match.size > 0 and match_ratio > 0.5: # Use a threshold for confidence
            # If a good match is found, refine start and end characters within the ASR segment
            ayah_match_start_char = match.a
            ayah_match_end_char = match.a + match.size # This is start char in asr_text

            # Update current_segment_char_idx for the next iteration (next ayah)
            current_segment_char_idx = ayah_match_end_char + 1 # Move past this ayah's match for next search
            
        # Calculate time for this ayah's segment in ASR
        # This is where we need to be careful with overall segment time
        
        # Calculate time boundaries for the current portion of ASR text that matches the Ayah
        effective_segment_duration = main_asr_segment_end - main_asr_segment_start
        
        # Character-based start/end of the current ayah's ASR match within the full ASR text
        # This assumes a linear distribution of time per character across the whole ASR segment.
        # This is an approximation.
        if len(current_segment_text_normalized) > 0:
            char_duration = effective_segment_duration / len(current_segment_text_normalized)
            ayah_segment_start_time = main_asr_segment_start + (ayah_match_start_char * char_duration)
            ayah_segment_end_time = main_asr_segment_start + (ayah_match_end_char * char_duration)
        else:
            ayah_segment_start_time = main_asr_segment_start
            ayah_segment_end_time = main_asr_segment_end
            
        # Distribute time among words within this Ayah
        timestamped_gt_words = distribute_time_proportionally(
            [{**w, 'text': w["text"]} for w in gt_words_for_this_ayah], # Use uthmani text (already in 'text' key) for proportional distribution
            ayah_segment_start_time,
            ayah_segment_end_time
        )
        
        # Populate word_timestamps with the now timestamped GT words
        ayah_obj_dict["word_timestamps"] = []
        for ts_word_data in timestamped_gt_words:
            # Reconstruct ts_word with original Quranic text and new timestamps
            original_word_data = next((w for w in gt_words_for_this_ayah if w["text"] == ts_word_data["text"]), None)
            if original_word_data:
                ayah_obj_dict["word_timestamps"].append({
                    "word_quranic": original_word_data["text"],
                    "char_offset_quranic_start": original_word_data["char_offset_start"],
                    "char_offset_quranic_end": original_word_data["char_offset_end"],
                    "word_asr": ts_word_data.get("text", ""), # Use the text used for ASR matching as word_asr
                    "start_time": ts_word_data["start_time"],
                    "end_time": ts_word_data["end_time"],
                    "asr_confidence": None, # Cannot get word-level confidence from segment-level ASR
                    "match_type": "proportional_distribution"
                })
            else:
                # Fallback if original_word_data not found (shouldn't happen with correct logic)
                ayah_obj_dict["word_timestamps"].append({
                    "word_quranic": ts_word_data["text"], # Fallback
                    "char_offset_quranic_start": None,
                    "char_offset_quranic_end": None,
                    "word_asr": ts_word_data.get("text", ""),
                    "start_time": ts_word_data["start_time"],
                    "end_time": ts_word_data["end_time"],
                    "asr_confidence": None,
                    "match_type": "proportional_distribution_fallback"
                })
    # 5. Final Output
    final_output_data = {
        "source_media_file": str(media_path.name),
        "asr_model_used": f"Base: {base_model_id}, LoRA: {lora_model_id if lora_model_id else 'None'} (via HF Pipeline)",
        "detected_surah": final_surah,
        "detected_start_ayah": final_start_ayah,
        "detected_end_ayah": final_end_ayah,
        "full_transcription_from_asr": full_asr_text,
        "ayah_data": result_ayah_data,
        "processing_summary": {
            "total_ayahs_processed": len(result_ayah_data),
            "asr_timestamped_segments_count": len(asr_segments_with_ts),
            "gt_words_count_in_range": len(all_quran_gt_words_structured),
            "approx_word_timestamps_generated_count": sum(len(ayah["word_timestamps"]) for ayah in result_ayah_data), # Count of words with estimated timestamps
            "errors_and_notes": processing_errors
        }
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output_data, f, indent=2, ensure_ascii=False)
    log.info(f"Timestamp generation complete. Output saved to: {output_path}")

    if temp_audio_file and temp_audio_file.exists():
        try: temp_audio_file.unlink(missing_ok=True)
        except OSError as e: log.warning(f"Could not delete temp audio {temp_audio_file}: {e}")

# --- Argparse and Main Execution ---
async def main():
    parser = argparse.ArgumentParser(description="Generate Quran timestamps from audio/video media.")
    parser.add_argument("media_file", type=Path, help="Path to the audio or video file.")
    parser.add_argument("--output_file", "-o", type=Path, default=None,
                        help="Path to save the JSON output. Defaults to media_file_timestamps.json in CLI output dir.")
    parser.add_argument("--surah_hint", type=int, help="Optional: Surah number hint (1-114).")
    parser.add_argument("--start_ayah_hint", type=int, help="Optional: Starting Ayah number hint.")
    parser.add_argument("--end_ayah_hint", type=int, help="Optional: Ending Ayah number hint (inclusive).")
    parser.add_argument("--translation_key", "-t", type=str, default=None,
                        choices=list(TRANSLATION_INFO.keys()), help="Key of the translation to include.")
    parser.add_argument("--tafseer_key", "-f", type=str, default=None,
                        choices=list(TAFSEER_INFO.keys()), help="Key of the Tafseer to include.")
    parser.add_argument("--min_match_ratio", type=float, default=0.4, # Lowered default
                        help="Minimum similarity ratio for auto-detection (0.1-1.0).")
    parser.add_argument("--base_model_id", type=str, default="openai/whisper-large-v2",
                        help="Base Whisper model ID from Hugging Face.")
    parser.add_argument("--lora_model_id", type=str, default=None, # Default to None to disable it
                        help="LoRA adapter model ID. Set to 'None' or empty to disable LoRA.")
    parser.add_argument("--force_cache_refresh", action="store_true",
                        help="Force fetching Quran text/translation/tafseer from API, ignoring cache.")
    parser.add_argument("--cpu", action="store_true", help="Force ASR to run on CPU, even if GPU is available.")
    parser.add_argument("--hf_token", type=str, default=None, help="Hugging Face API token for private/gated models.")
    parser.add_argument("--pipeline_batch_size", type=int, default=8, help="Batch size for ASR pipeline processing.")
    parser.add_argument("--pipeline_chunk_length_s", type=int, default=30, help="Chunk length in seconds for ASR pipeline.")

    args = parser.parse_args()

    if not args.media_file.exists():
        log.error(f"Media file not found: {args.media_file}")
        return

    output_file_path = args.output_file
    if output_file_path is None:
        output_file_path = OUTPUT_DIR / f"{args.media_file.stem}_timestamps.json"
    
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    lora_id_to_pass = args.lora_model_id
    if lora_id_to_pass and (lora_id_to_pass.lower() == 'none' or lora_id_to_pass.strip() == ''):
        lora_id_to_pass = None

    token = args.hf_token
    if not token:
        import os
        token = os.getenv("HUGGING_FACE_TOKEN")
        if token: log.info("Using Hugging Face token from HUGGING_FACE_TOKEN environment variable.")

    await generate_timestamps_for_media(
        media_path=args.media_file,
        output_path=output_file_path,
        surah_hint=args.surah_hint,
        start_ayah_hint=args.start_ayah_hint,
        end_ayah_hint=args.end_ayah_hint,
        translation_key=args.translation_key,
        tafseer_key=args.tafseer_key,
        min_match_ratio=args.min_match_ratio,
        base_model_id=args.base_model_id,
        lora_model_id=lora_id_to_pass,
        force_cache_refresh=args.force_cache_refresh,
        use_gpu_if_available=not args.cpu,
        hf_token=token,
        pipeline_batch_size=args.pipeline_batch_size,
        pipeline_chunk_length_s=args.pipeline_chunk_length_s
    )

if __name__ == "__main__":
    asyncio.run(main())