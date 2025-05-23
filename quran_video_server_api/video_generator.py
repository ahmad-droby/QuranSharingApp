# video_generator.py
import logging
import time
import traceback
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Corrected MoviePy imports as requested
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    ImageClip, ColorClip
)
# Import Loop class specifically
from moviepy.video.fx.Loop import Loop as moviepy_loop # Renaming to avoid conflict

# If you need ImageMagick for complex text, uncomment and set the path
# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": r"/path/to/your/magick"})

# Local imports
from text_utils import prepare_arabic_text
from config import (
    DEFAULT_FONT_ARABIC, DEFAULT_FONT_ENGLISH, DEFAULT_FONT_SIZE_ARABIC,
    DEFAULT_FONT_SIZE_ENGLISH, DEFAULT_TEXT_COLOR, VIDEO_FPS, VIDEO_CODEC,
    AUDIO_CODEC, BACKGROUND_MAP, TEMP_DIR, AUDIO_CROSSFADE_MS
)

# Pydub for audio manipulation
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Audio Silence Trimming Function ---
# (No changes needed in trim_silence)
def trim_silence(src: Path, silence_thresh: int = -40, min_sil_len: int = 100) -> Optional[AudioSegment]:
    # ... (function content remains the same) ...
    if not src.exists():
        log.warning(f"Audio source for trimming not found: {src}")
        return None
    try:
        audio = AudioSegment.from_file(str(src))
        non_silent_ranges = detect_nonsilent(
            audio, min_silence_len=min_sil_len, silence_thresh=silence_thresh
        )
        if not non_silent_ranges:
            log.warning(f"No non-silent parts detected in: {src.name} (using threshold {silence_thresh}dB, min length {min_sil_len}ms). Returning original.")
            return audio
        start_trim = non_silent_ranges[0][0]
        end_trim = non_silent_ranges[-1][1]
        trimmed_audio = audio[start_trim:end_trim]
        log.debug(f"Trimmed {src.name}: Original duration {len(audio)}ms, Trimmed duration {len(trimmed_audio)}ms")
        return trimmed_audio
    except Exception as e:
        log.error(f"Error processing or trimming audio file {src}: {e}", exc_info=True)
        return None

# --- Revised Audio Concatenation using Pydub with Crossfade AND Padding ---
# (No changes needed in concatenate_audio_files_smooth)
def concatenate_audio_files_smooth(
    audio_file_paths: List[Path],
    job_id: str,
    output_dir: Path = TEMP_DIR,
    crossfade_duration: int = AUDIO_CROSSFADE_MS,
    padding_duration_ms: int = 100
) -> Optional[Path]:
    # ... (function content remains the same) ...
    if not audio_file_paths:
        log.warning(f"[Job {job_id}] No audio files provided for concatenation.")
        return None

    output_path = output_dir / f"{job_id}_concatenated_audio.mp3"
    log.info(f"[Job {job_id}] Starting smooth audio concatenation for {len(audio_file_paths)} files -> {output_path.name} (Crossfade: {crossfade_duration}ms, Padding: {padding_duration_ms}ms)")

    processed_segments: List[AudioSegment] = []
    for i, file_path in enumerate(audio_file_paths):
        log.debug(f"[Job {job_id}] Processing segment {i+1}/{len(audio_file_paths)}: {file_path.name}")
        if not file_path.exists():
            log.error(f"[Job {job_id}] Audio file missing during concatenation: {file_path}")
            raise FileNotFoundError(f"Required audio file not found: {file_path}")
        trimmed_segment = trim_silence(file_path)
        if trimmed_segment:
            processed_segments.append(trimmed_segment)
        else:
            log.warning(f"[Job {job_id}] Skipping file due to trimming failure or silence: {file_path}")

    if not processed_segments:
        log.warning(f"[Job {job_id}] No valid audio segments found after trimming. Cannot concatenate.")
        return None

    try:
        final_audio: AudioSegment = processed_segments[0]
        if len(processed_segments) > 1:
            log.info(f"[Job {job_id}] Applying {crossfade_duration}ms crossfade between {len(processed_segments)} segments.")
            for segment in processed_segments[1:]:
                 safe_crossfade = max(1, min(crossfade_duration, len(final_audio), len(segment)))
                 if safe_crossfade < crossfade_duration:
                     log.warning(f"[Job {job_id}] Reduced crossfade to {safe_crossfade}ms for segment join due to short segment length(s).")
                 final_audio = final_audio.append(segment, crossfade=safe_crossfade)

        if padding_duration_ms > 0:
            final_audio += AudioSegment.silent(duration=padding_duration_ms)
            log.info(f"[Job {job_id}] Added {padding_duration_ms}ms silence padding to the end of concatenated audio.")

        final_duration_s = len(final_audio) / 1000.0
        log.info(f"[Job {job_id}] Exporting final concatenated audio (incl. padding) (Pydub Duration: {final_duration_s:.8f}s) to {output_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        final_audio.export(str(output_path), format="mp3", codec='libmp3lame')

        log.info(f"[Job {job_id}] Successfully concatenated audio smoothly to: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"[Job {job_id}] Failed to concatenate audio files with pydub: {e}", exc_info=True)
        if output_path.exists():
            try: output_path.unlink()
            except OSError: pass
        return None


# --- Main Video Generation Function (with corrected imports and loop) ---
def generate_quran_video(
    arabic_texts: List[str],
    translation_texts: List[str],
    all_word_timestamps: List[Dict[str, Any]],
    concatenated_audio_path: Path,
    background_id: str,
    output_path: Path,
    job_id: str
) -> bool:
    """
    Generates the Quran video with synchronized text overlays for multiple Ayahs.
    Uses corrected imports and loop application method.
    Applies duration fixes to prevent boundary errors during rendering.
    Returns True on success, False on failure.
    """
    start_gen_time = time.time()
    log.info(f"[Job {job_id}] Starting video generation process for {len(arabic_texts)} Ayahs.")
    log.info(f"[Job {job_id}] Output: {output_path.name}")
    log.info(f"[Job {job_id}] Using audio: {concatenated_audio_path.name}")
    log.info(f"[Job {job_id}] Using background ID: {background_id}")

    clips_to_close = []
    audio_clip = None
    background_clip = None
    final_clip = None
    arabic_bg_template = None
    english_bg_template = None

    def safe_close(clip):
        if clip and hasattr(clip, 'close'):
            try: clip.close()
            except Exception as e_close: log.warning(f"[Job {job_id}] Error closing clip {type(clip)}: {e_close}")

    try:
        # --- 1. Load Background ---
        if background_id not in BACKGROUND_MAP: raise ValueError(f"Invalid background ID: {background_id}")
        bg_config = BACKGROUND_MAP[background_id]; bg_path = Path(bg_config["path"])
        if not bg_path.is_file(): raise FileNotFoundError(f"Background file missing: {bg_path}")
        log.info(f"[Job {job_id}] Loading background: {bg_path} (Type: {bg_config['type']})")
        bg_type = bg_config['type'].lower()
        if bg_type == "video": background_clip = VideoFileClip(str(bg_path))
        elif bg_type == "image": background_clip = ImageClip(str(bg_path)).with_duration(1) # Use with_duration directly on ImageClip
        else: raise ValueError(f"Unsupported background type: {bg_config['type']}")
        clips_to_close.append(background_clip)

        # --- 2. Load Concatenated Audio ---
        log.info(f"[Job {job_id}] Loading smoothly concatenated audio: {concatenated_audio_path}")
        if not concatenated_audio_path.exists(): raise FileNotFoundError(f"Concatenated audio file disappeared: {concatenated_audio_path}")
        audio_clip = AudioFileClip(str(concatenated_audio_path))
        clips_to_close.append(audio_clip)
        audio_length_moviepy = audio_clip.duration
        log.info(f"[Job {job_id}] Audio duration reported by MoviePy (incl. padding): {audio_length_moviepy:.8f} seconds")

        # --- 3. Determine Target Video Duration ---
        target_video_duration = audio_length_moviepy
        last_word_end_time = 0.0
        if all_word_timestamps:
            try:
                all_word_timestamps.sort(key=lambda x: x['start_time'])
                if all_word_timestamps:
                    last_word_end_time = all_word_timestamps[-1]['end_time']
                    log.info(f"[Job {job_id}] Last word timestamp ends at: {last_word_end_time:.8f}s")
                    if last_word_end_time > target_video_duration:
                         log.warning(f"[Job {job_id}] Last word timestamp ({last_word_end_time:.4f}s) exceeds loaded audio duration ({target_video_duration:.4f}s).")
            except Exception as ts_err: log.warning(f"[Job {job_id}] Error processing timestamps: {ts_err}. Using audio duration.")
        else: log.warning(f"[Job {job_id}] No timestamps. Using audio duration.")
        if target_video_duration <= 0: raise ValueError("Video duration must be positive.")
        log.info(f"[Job {job_id}] Target video duration set to: {target_video_duration:.8f}s")

        # --- 4. Adjust Background Duration & Size ---
        try: w_bg, h_bg = background_clip.size
        except Exception as size_err: raise ValueError(f"Failed to get initial background dimensions: {size_err}")
        if isinstance(background_clip, ImageClip):
            background_clip = background_clip.with_duration(target_video_duration).with_size((w_bg, h_bg))
        elif background_clip.duration < target_video_duration:
            log.warning(f"[Job {job_id}] Background video shorter ({background_clip.duration:.2f}s) than required ({target_video_duration:.2f}s). Looping.")
            # --- *** CORRECTED LOOP APPLICATION *** ---
            looper = moviepy_loop(duration=target_video_duration)
            background_clip = looper.apply(background_clip)
            # --- *** END CORRECTION *** ---
        elif background_clip.duration > target_video_duration:
             log.info(f"[Job {job_id}] Background video longer ({background_clip.duration:.2f}s) than required ({target_video_duration:.2f}s). Trimming.")
             # Use subclip method directly on VideoFileClip/ImageClip
             background_clip = background_clip.subclip(0, target_video_duration)
        if not background_clip.size or background_clip.size[0] is None or background_clip.size[1] is None:
             log.warning(f"[Job {job_id}] Background clip lost size info. Resetting to: ({w_bg}, {h_bg})")
             background_clip = background_clip.with_size((w_bg, h_bg)) # Use with_size
        w, h = background_clip.size
        if not w or not h: raise ValueError("Background clip has invalid size after duration adjustments.")
        log.info(f"[Job {job_id}] Video dimensions set to: {w}x{h}")

        # --- 5. Create Text Clip Templates ---
        box_width = int(w * 0.9); box_height_arabic = int(DEFAULT_FONT_SIZE_ARABIC * 3.0); box_height_english = int(DEFAULT_FONT_SIZE_ENGLISH * 2.5)
        bg_color_tuple = (0, 0, 0); bg_opacity = 0.6
        arabic_bg_template = ColorClip(size=(box_width, box_height_arabic), color=bg_color_tuple, is_mask=False).with_opacity(bg_opacity)
        clips_to_close.append(arabic_bg_template)
        english_bg_template = ColorClip(size=(box_width, box_height_english), color=bg_color_tuple, is_mask=False).with_opacity(bg_opacity)
        clips_to_close.append(english_bg_template)

        # --- 6. Create Timed Text Clips ---
        text_clips_generated = []
        num_ayahs = len(arabic_texts)
        log.info(f"[Job {job_id}] Starting generation of {num_ayahs} Ayah text overlays...")
        for i in range(num_ayahs):
            # (This inner loop logic for creating text clips remains the same)
            ayah_start_time = -1.0; ayah_duration = 0.0
            try:
                arabic_text = arabic_texts[i]; translation_text = translation_texts[i]
                ayah_timestamps = [ts for ts in all_word_timestamps if ts.get('ayah_index') == i]
                if not ayah_timestamps: log.warning(f"[Job {job_id}] Ayah index {i}: No timestamps. Skipping text."); continue
                ayah_start_time = min(ts['start_time'] for ts in ayah_timestamps)
                ayah_end_time = max(ts['end_time'] for ts in ayah_timestamps)
                ayah_duration = ayah_end_time - ayah_start_time

                if ayah_duration <= 0: log.warning(f"[Job {job_id}] Ayah index {i}: Invalid duration ({ayah_duration:.4f}s). Skipping."); continue
                if ayah_start_time < 0: log.warning(f"[Job {job_id}] Ayah index {i}: Invalid start ({ayah_start_time:.4f}s). Skipping."); continue
                if ayah_start_time >= target_video_duration: log.warning(f"[Job {job_id}] Ayah index {i}: Start ({ayah_start_time:.4f}s) >= target ({target_video_duration:.4f}s). Skipping."); continue

                calculated_text_end_time = ayah_start_time + ayah_duration
                if calculated_text_end_time > target_video_duration:
                     original_duration = ayah_duration
                     ayah_duration = target_video_duration - ayah_start_time
                     log.warning(f"[Job {job_id}] Ayah index {i}: Truncated text duration from {original_duration:.4f}s to {ayah_duration:.4f}s to fit target.")
                     if ayah_duration <= 0: log.warning(f"[Job {job_id}] Ayah index {i}: Zero duration after truncation. Skipping."); continue

                log.debug(f"[Job {job_id}] Ayah index {i}: Text timing: Start={ayah_start_time:.4f}, Final Duration={ayah_duration:.4f}")

                display_arabic_text = prepare_arabic_text(arabic_text)
                arabic_bg = arabic_bg_template.copy().with_duration(ayah_duration) # Use with_duration
                txt_arabic = TextClip(text=display_arabic_text, font_size=DEFAULT_FONT_SIZE_ARABIC, color=DEFAULT_TEXT_COLOR, font=DEFAULT_FONT_ARABIC, bg_color=None, size=(int(box_width * 0.95), None), method='caption', text_align='center').with_position(('center', 'center')).with_duration(ayah_duration)
                arabic_clip_with_bg = CompositeVideoClip([arabic_bg, txt_arabic], size=arabic_bg.size).with_position(('center', h * 0.15)) # Use with_position
                timed_arabic_clip = arabic_clip_with_bg.with_start(ayah_start_time) # Use with_start
                text_clips_generated.append(timed_arabic_clip)

                english_bg = english_bg_template.copy().with_duration(ayah_duration)
                txt_english = TextClip(text=translation_text, font_size=DEFAULT_FONT_SIZE_ENGLISH, color=DEFAULT_TEXT_COLOR, font=DEFAULT_FONT_ENGLISH, bg_color=None, size=(int(box_width * 0.95), None), method='caption', text_align='center').with_position(('center', 'center')).with_duration(ayah_duration)
                english_clip_with_bg = CompositeVideoClip([english_bg, txt_english], size=english_bg.size).with_position(('center', h * 0.70))
                timed_english_clip = english_clip_with_bg.with_start(ayah_start_time)
                text_clips_generated.append(timed_english_clip)

            except KeyError as ke: log.error(f"[Job {job_id}] Ayah index {i}: Missing key: {ke}. Skipping.")
            except Exception as text_err: log.error(f"[Job {job_id}] Ayah index {i}: Failed clip creation: {text_err}", exc_info=True)
        log.info(f"[Job {job_id}] Generated {len(text_clips_generated)} timed text overlay clips.")

        # --- 7. Composite Final Video ---
        if not background_clip: raise ValueError("Background invalid.")
        log.info(f"[Job {job_id}] Compositing final video...")
        final_layers = [background_clip.with_duration(target_video_duration)] + text_clips_generated # Use with_duration
        final_clip = CompositeVideoClip(final_layers, size=(w, h))
        if not audio_clip: raise ValueError("Audio invalid.")
        final_clip = final_clip.with_audio(audio_clip) # Use with_audio

        # --- Apply Final Duration Fix for Writing ---
        safe_writing_duration = target_video_duration - (1 / VIDEO_FPS)
        safe_writing_duration = max(0, safe_writing_duration)
        log.info(f"[Job {job_id}] Final target duration (before precision adjust): {target_video_duration:.8f}s")
        log.info(f"[Job {job_id}] Setting final clip duration FOR WRITING (adjusted): {safe_writing_duration:.8f}s")
        final_clip = final_clip.with_duration(safe_writing_duration)
        clips_to_close.append(final_clip)

        # --- 8. Write Final Output Video ---
        output_path.parent.mkdir(parents=True, exist_ok=True)
        log.info(f"[Job {job_id}] Writing final video (Effective Write Duration: {final_clip.duration:.4f}s) to: {output_path}")
        final_clip.write_videofile(
            str(output_path), fps=VIDEO_FPS, codec=VIDEO_CODEC, audio_codec=AUDIO_CODEC,
            threads=os.cpu_count() or 4, preset='medium', logger='bar', bitrate="5000k"
        )

        end_gen_time = time.time()
        log.info(f"[Job {job_id}] Video generation successful! Time: {end_gen_time - start_gen_time:.2f}s")
        return True

    except Exception as e:
        log.error(f"[Job {job_id}] Unexpected error during video generation: {e}", exc_info=True)
        return False
    finally:
        # --- Cleanup ---
        log.info(f"[Job {job_id}] Cleaning up MoviePy resources...")
        for clip in reversed(clips_to_close): safe_close(clip)
        for clip in text_clips_generated:
            if isinstance(clip, CompositeVideoClip) and hasattr(clip, 'clips'):
                for sub_clip in getattr(clip, 'clips', []): safe_close(sub_clip)
            safe_close(clip)
        log.info(f"[Job {job_id}] MoviePy resource cleanup finished.")
        # Reminder: Calling script handles temp audio deletion
