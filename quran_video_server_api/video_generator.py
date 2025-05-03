# video_generator.py
import logging
import time
import traceback
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from moviepy import ( # Use moviepy.editor for easier access
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, concatenate_audioclips, ImageClip, ColorClip
)

from moviepy.video.fx.Loop import Loop

# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": r"/path/to/your/magick"})

from text_utils import prepare_arabic_text
from config import (
    DEFAULT_FONT_ARABIC, DEFAULT_FONT_ENGLISH, DEFAULT_FONT_SIZE_ARABIC,
    DEFAULT_FONT_SIZE_ENGLISH, DEFAULT_TEXT_COLOR, VIDEO_FPS, VIDEO_CODEC,
    AUDIO_CODEC, BACKGROUND_MAP, TEMP_DIR # AUDIO_CODEC is for the final video
)

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def trim_silence(src: Path, silence_thresh=-40, min_sil_len=100) -> Optional[AudioSegment]:
    """
    Trim leading/trailing silence using pydub.
    """
    if not src.exists():
        return None
    audio = AudioSegment.from_file(str(src))
    non_silent_ranges = detect_nonsilent(audio, min_silence_len=min_sil_len, silence_thresh=silence_thresh)
    if not non_silent_ranges:
        return None
    # Take the full start/end range of the non-silent portions
    start_trim = non_silent_ranges[0][0]
    end_trim = non_silent_ranges[-1][1]
    return audio[start_trim:end_trim]

# --- Helper Function for Audio Concatenation ---
def concatenate_audio_files(
    audio_file_paths: List[Path],
    job_id: str,
    output_dir: Path = TEMP_DIR # Store concatenated audio also in temp
) -> Optional[Path]:
    """Concatenates multiple audio files into one."""
    if not audio_file_paths:
        log.warning(f"[Job {job_id}] No audio files provided for concatenation.")
        return None

    # Define the output path for the concatenated temporary audio file
    output_path = output_dir / f"{job_id}_concatenated_audio.mp3"
    clips_to_concat = []
    log.info(f"[Job {job_id}] Starting audio concatenation for {len(audio_file_paths)} files -> {output_path.name}")

    try:
        for file_path in audio_file_paths:
            if not file_path.exists():
                log.error(f"[Job {job_id}] Audio file missing during concatenation: {file_path}")
                # Cleanup already loaded clips before raising
                for clip in clips_to_concat:
                    try:
                        clip.close()
                    except Exception: pass # Ignore errors during cleanup cascade
                raise FileNotFoundError(f"Required audio file not found: {file_path}")
            
            trimmed_segment = trim_silence(file_path)
            if not trimmed_segment:
                log.error(f"[Job {job_id}] Unable to trim or file empty: {file_path}")
                # Cleanup already loaded clips before raising
                for clip in clips_to_concat:
                    try:
                        clip.close()
                    except Exception: pass # Ignore errors during cleanup cascade
                raise FileNotFoundError(f"Required audio file not found: {file_path}")
            
            # Apply fade in and fade out to the trimmed segment
            trimmed_segment = trimmed_segment.fade_in(300).fade_out(300)

            # Export the trimmed audio before loading as AudioFileClip
            trimmed_path = output_dir / f"{file_path.stem}_trimmed_temp.mp3"
            trimmed_segment.export(trimmed_path, format="mp3")
            clips_to_concat.append(AudioFileClip(str(trimmed_path)))

        if not clips_to_concat:
            log.warning(f"[Job {job_id}] No valid audio clips loaded for concatenation.")
            return None

        final_audio = concatenate_audioclips(clips_to_concat)

        # --- *** FIX APPLIED HERE *** ---
        # Write the temporary concatenated audio file using the correct codec for MP3
        final_audio.write_audiofile(
            str(output_path),
            codec='libmp3lame', # Explicitly use MP3 codec for .mp3 file
            logger=None # Suppress verbose progress bars for this intermediate step
        )
        # --- *** END FIX *** ---

        log.info(f"[Job {job_id}] Successfully concatenated audio to: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"[Job {job_id}] Failed to concatenate audio files: {e}", exc_info=True)
        if output_path.exists(): # Attempt cleanup on failure
            try: output_path.unlink()
            except OSError: pass
        return None
    finally:
        # Close all individual clips loaded during concatenation
        for clip in clips_to_concat:
            try:
                clip.close()
            except Exception as e_close:
                log.warning(f"[Job {job_id}] Error closing an audio clip during concatenation cleanup: {e_close}")
        # Note: Deletion of the *original* individual segment files
        # is handled in the main process function's finally block.


# --- Updated Video Generation Function ---
def generate_quran_video(
    arabic_texts: List[str], # List of Arabic text per Ayah
    translation_texts: List[str], # List of Translation text per Ayah
    all_word_timestamps: List[Dict[str, Any]], # Combined, OFFSET timestamps with 'ayah_index'
    concatenated_audio_path: Path, # Path to the SINGLE *concatenated* audio (e.g., the .mp3)
    background_id: str,
    output_path: Path, # Final video output path (e.g., .mp4)
    job_id: str # For logging
) -> bool:
    """
    Generates the Quran video for MULTIPLE AYAHs with text synchronized to audio.
    Assumes timestamps are offset and audio is concatenated.
    Returns True on success, False on failure.
    """
    start_gen_time = time.time()
    log.info(f"[Job {job_id}] Starting video generation for {len(arabic_texts)} Ayahs ({output_path.name}) using audio {concatenated_audio_path.name}")

    audio_clip = None
    background_clip = None
    final_clip = None
    text_clips_generated = [] # Keep track of clips for cleanup

    try:
        # --- 1. Load Background ---
        if background_id not in BACKGROUND_MAP:
             log.error(f"[Job {job_id}] Background ID '{background_id}' not found in config.")
             raise ValueError(f"Invalid background ID: {background_id}")
        bg_config = BACKGROUND_MAP[background_id]
        bg_path = Path(bg_config["path"])

        if not bg_path.is_file():
             log.error(f"[Job {job_id}] Background file not found: {bg_path}")
             raise FileNotFoundError(f"Background file missing: {bg_path}")

        log.info(f"[Job {job_id}] Loading background: {bg_path} (Type: {bg_config['type']})")
        if bg_config["type"] == "video":
            background_clip = VideoFileClip(str(bg_path))
        elif bg_config["type"] == "image":
            background_clip = ImageClip(str(bg_path))
        else:
            log.error(f"[Job {job_id}] Unsupported background type: {bg_config['type']}")
            raise ValueError(f"Unsupported background type: {bg_config['type']}")


        # --- 2. Load Concatenated Audio ---
        log.info(f"[Job {job_id}] Loading concatenated audio: {concatenated_audio_path}")
        if not concatenated_audio_path.exists():
             log.error(f"[Job {job_id}] Concatenated audio file is missing: {concatenated_audio_path}")
             raise FileNotFoundError("Concatenated audio file disappeared")
        # Load the temporary concatenated audio file (e.g., the .mp3)
        audio_clip = AudioFileClip(str(concatenated_audio_path))
        audio_length = audio_clip.duration

        # Determine total duration from the *last* timestamp
        if not all_word_timestamps:
            log.error(f"[Job {job_id}] No word timestamps provided, cannot determine video duration.")
            raise ValueError("Missing timestamps for video generation")

        all_word_timestamps.sort(key=lambda x: x['start_time']) # Ensure sorted
        total_duration = all_word_timestamps[-1]['end_time']
        capped_duration = min(total_duration, audio_length)
        log.info(f"[Job {job_id}] Determined total clip duration from timestamps: {total_duration:.2f} seconds")

        # Adjust background duration to match the total duration
        if isinstance(background_clip, ImageClip):
            background_clip = background_clip.with_duration(capped_duration)
        elif background_clip.duration < capped_duration:
            log.warning(f"[Job {job_id}] Background video shorter ({background_clip.duration:.2f}s) than required ({capped_duration:.2f}s). Looping background.")
            loop = Loop(duration=capped_duration)
            background_clip = loop.apply(background_clip) 
        elif background_clip.duration > capped_duration:
             log.info(f"[Job {job_id}] Background video longer ({background_clip.duration:.2f}s) than required ({capped_duration:.2f}s). Trimming background.")
             background_clip = background_clip.subclipped(0, capped_duration)


        # --- 3. Create Text Clips for EACH Ayah ---
        w, h = background_clip.size
        box_width = int(w * 0.9)
        # Estimate heights - might need adjustment based on font/content
        box_height_arabic = int(DEFAULT_FONT_SIZE_ARABIC * 2.5)
        box_height_english = int(DEFAULT_FONT_SIZE_ENGLISH * 2.0)

        arabic_bg_template = ColorClip(size=(box_width, box_height_arabic), color=(0, 0, 0), is_mask=False).with_opacity(0.6)
        english_bg_template = ColorClip(size=(box_width, box_height_english), color=(0, 0, 0), is_mask=False).with_opacity(0.6)

        num_ayahs = len(arabic_texts)
        for i in range(num_ayahs):
            arabic_text = arabic_texts[i]
            translation_text = translation_texts[i]

            # Find the start and end time for *this specific Ayah* using the 'ayah_index' in offset timestamps
            ayah_timestamps = [ts for ts in all_word_timestamps if ts.get('ayah_index') == i]
            if not ayah_timestamps:
                log.warning(f"[Job {job_id}] No timestamps found for Ayah index {i}. Skipping text display for this Ayah.")
                continue

            # Timestamps for the Ayah are already offset
            ayah_start_time = min(ts['start_time'] for ts in ayah_timestamps)
            ayah_end_time = max(ts['end_time'] for ts in ayah_timestamps)
            ayah_duration = ayah_end_time - ayah_start_time

            if ayah_duration <= 0:
                log.warning(f"[Job {job_id}] Invalid duration ({ayah_duration:.2f}s) calculated for Ayah index {i}. Skipping text display.")
                continue

            log.debug(f"[Job {job_id}] Processing Ayah index {i}: Start={ayah_start_time:.2f}, End={ayah_end_time:.2f}, Dur={ayah_duration:.2f}")

            display_arabic_text = prepare_arabic_text(arabic_text)

            # --- Arabic Text Clip for this Ayah ---
            # Create copies of the background templates for this Ayah
            arabic_bg = arabic_bg_template.copy()
            txt_arabic = TextClip(
                text=display_arabic_text, # Use txt= instead of text= for older moviepy? Check documentation if issues.
                font_size=DEFAULT_FONT_SIZE_ARABIC,
                color=DEFAULT_TEXT_COLOR,
                font=DEFAULT_FONT_ARABIC,
                bg_color=None, # Transparent background for text itself
                size=(int(box_width * 0.95), None), # Constrain width, auto height
                method='caption', # Handles word wrapping
                text_align='center',
            ).with_position(('center', 'center'))

            arabic_clip_with_bg = CompositeVideoClip([arabic_bg, txt_arabic], size=arabic_bg.size)
            arabic_clip_with_bg = arabic_clip_with_bg.with_position(('center', 0.15 * h)) # Position box on screen
            # Set timing for THIS Ayah's Arabic text based on offset timestamps
            timed_arabic_clip = arabic_clip_with_bg.with_start(ayah_start_time).with_duration(ayah_duration)
            text_clips_generated.append(timed_arabic_clip)


            # --- English Text Clip for this Ayah ---
            english_bg = english_bg_template.copy()
            txt_english = TextClip(
                text=translation_text, # Use txt=
                font_size=DEFAULT_FONT_SIZE_ENGLISH,
                color=DEFAULT_TEXT_COLOR,
                font=DEFAULT_FONT_ENGLISH,
                bg_color=None,
                size=(int(box_width * 0.95), None), # Constrain width, auto height
                method='caption',
                text_align='center',
            ).with_position(('center', 'center'))

            english_clip_with_bg = CompositeVideoClip([english_bg, txt_english], size=english_bg.size)
            english_clip_with_bg = english_clip_with_bg.with_position(('center', 0.70 * h)) # Position box on screen
            # Set timing for THIS Ayah's English text based on offset timestamps
            timed_english_clip = english_clip_with_bg.with_start(ayah_start_time).with_duration(ayah_duration)
            text_clips_generated.append(timed_english_clip)


            # --- Word Highlighting (Placeholder - requires complex implementation) ---
            # Iterate through ayah_timestamps for word highlights within this Ayah's window
            # Calculation of exact word position on screen within wrapped text is non-trivial.
            # ...


        log.info(f"[Job {job_id}] Generated {len(text_clips_generated)} timed text clips for {num_ayahs} Ayahs.")

        # --- 4. Composite Everything ---
        # Layer the background and ALL timed text clips
        final_clip = CompositeVideoClip([background_clip] + text_clips_generated, size=background_clip.size)

        # Set the full concatenated audio (loaded earlier)
        final_clip = final_clip.with_audio(audio_clip)
        # Ensure the final video duration matches the calculated total duration
        # (This might slightly trim audio if timestamps end before audio file does)
        final_clip = final_clip.with_duration(capped_duration)


        # --- 5. Write Final Output Video ---
        log.info(f"[Job {job_id}] Writing final video to: {output_path}")
        # Use the AUDIO_CODEC from config ('aac') for the final MP4 video's audio track
        final_clip.write_videofile(
            str(output_path),
            fps=VIDEO_FPS,
            codec=VIDEO_CODEC,      # e.g., 'libx264'
            audio_codec=AUDIO_CODEC,  # e.g., 'aac' (Correct for MP4 container)
            threads=4, # Adjust based on your system
            preset='medium', # Faster options: 'fast', 'superfast', 'ultrafast'
            logger='bar' # Or None to disable progress bar
        )

        end_gen_time = time.time()
        log.info(f"[Job {job_id}] Video generation successful! Time taken: {end_gen_time - start_gen_time:.2f} seconds.")
        return True

    except Exception as e:
        log.error(f"[Job {job_id}] Video generation failed: {e}")
        log.error(traceback.format_exc())
        return False

    finally:
        # --- Cleanup MoviePy Resources ---
        log.info(f"[Job {job_id}] Cleaning up MoviePy resources...")
        try:
            # Close main clips
            if audio_clip: audio_clip.close()
            if background_clip: background_clip.close()
            if final_clip: final_clip.close()
            # Close individual text/composite clips generated in the loop
            for clip in text_clips_generated:
                 # CompositeVideoClip might need manual closure of its subclips if issues arise
                if hasattr(clip, 'close'):
                    clip.close()
        except Exception as e:
            log.warning(f"[Job {job_id}] Error during MoviePy clip cleanup: {e}")

        # --- IMPORTANT ---
        # Deletion of the TEMPORARY *concatenated* audio file (`concatenated_audio_path`)
        # is handled by the main process function (`process_video_generation`)'s finally block.
        # Do NOT delete it here.