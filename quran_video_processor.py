import json
import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
from typing import Optional, Tuple
import cv2 
import logging

import numpy as np # Added for logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__) # Logger for this module

from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, ColorClip # Added ColorClip
from PIL import Image, ImageDraw, ImageFont

# Define font directory and default font path
FONT_DIR = Path("quran_video_server_api/data/fonts")
DEFAULT_FONT_PATH = FONT_DIR / "Amiri/Amiri-Bold.ttf" # Changed back to Noto Sans

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Converts a hex color string (e.g., '#RRGGBB') to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def parse_rgba_to_tuple(rgba_str: str) -> Tuple[int, int, int, int]:
    # moviepy on_color expects (R, G, B) or (R, G, B, A) but sometimes gets str
    # This is a robust parsing for 'rgba(R,G,B,A)' or simple 'colorname'
    rgba_str = rgba_str.strip()
    if rgba_str.lower() in ['black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta']:
        # This is a simplification; for real application, map named colors to RGBA
        # For now, just return black for 'black', etc.
        if rgba_str.lower() == 'black': return (0,0,0,255)
        elif rgba_str.lower() == 'white': return (255,255,255,255)
        else: return (0,0,0,255) # Default to black for others
    
    if rgba_str.startswith('rgba(') and rgba_str.endswith(')'):
        values = rgba_str[5:-1].split(',')
        if len(values) == 4:
            try: return (int(values[0]), int(values[1]), int(values[2]), int(float(values[3]) * 255))
            except ValueError: pass
    elif rgba_str.startswith('rgb(') and rgba_str.endswith(')'):
        values = rgba_str[4:-1].split(',')
        if len(values) == 3:
            try: return (int(values[0]), int(values[1]), int(values[2]), 255) # Assuming opaque if RGB
            except ValueError: pass
    
    # Fallback for unrecognized formats (e.g., hex or simple color string)
    # Could expand this to handle full CSS color names / hex, but for simplicity:
    return (0, 0, 0, 255) # Default to opaque black

def render_text_to_image(
    text: str,
    font_path: Path,
    font_size: int,
    text_color_hex: str,
    stroke_color_hex: Optional[str] = None,
    stroke_width: float = 0
) -> Image.Image:
    """Renders Arabic text onto a PIL Image, detecting text size dynamically."""
    log.debug(f"render_text_to_image: Rendering text '{text}' with font '{font_path}' (size {font_size})")
    try:
        font = ImageFont.truetype(str(font_path), font_size)
        log.debug(f"render_text_to_image: Successfully loaded font '{font_path}'.")
    except IOError:
        log.warning(f"render_text_to_image: Font file not found: {font_path}. Falling back to default Pillow font.")
        font = ImageFont.load_default()
    except Exception as e:
        log.error(f"render_text_to_image: Error loading font {font_path}: {e}. Falling back to default Pillow font.", exc_info=True)
        font = ImageFont.load_default()

    # Calculate text size for accurate image dimensions
    test_img = Image.new('RGB', (1, 1)) # Dummy image for textbbox
    test_draw = ImageDraw.Draw(test_img)
    
    # Use textbbox for more accurate size. Removed 'direction="rtl"' here.
    # The 'textbbox' method may still implicitly handle direction based on font type.
    bbox = test_draw.textbbox((0, 0), text, font=font)
    
    text_actual_width = bbox[2] - bbox[0]
    text_actual_height = bbox[3] - bbox[1]
    
    log.debug(f"render_text_to_image: Calculated text dimensions: W={text_actual_width}, H={text_actual_height}")

    # Add padding around the text
    padding_x = 20
    padding_y = 10
    
    img_width = max(int(text_actual_width + (padding_x * 2)), 100) # Ensure a minimum width for small text
    img_height = int(text_actual_height + (padding_y * 2)) # Ensure integer for image creation

    # The image will be as wide as needed for the text. MoviePy will scale/position it.
    
    log.debug(f"render_text_to_image: Final image dimensions: W={img_width}, H={img_height}")

    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0)) # Transparent background
    draw = ImageDraw.Draw(img)
    
    # Determine text color and stroke color
    final_text_color = hex_to_rgb(text_color_hex)
    final_stroke_color = hex_to_rgb(stroke_color_hex) if stroke_color_hex else None
    
    # Calculate text drawing position to center it within the image
    x_draw = (img_width - text_actual_width) / 2
    y_draw = (img_height - text_actual_height) / 2
    
    log.debug(f"render_text_to_image: Drawing text at ({x_draw:.2f}, {y_draw:.2f})")
    log.debug(f"render_text_to_image: text='{text[:50]}', font='{str(font_path).split('/')[-1]}', fill={final_text_color}, stroke={final_stroke_color}, stroke_width={stroke_width}")

    # Draw the text. Removed 'direction="rtl"' here as well.
    draw.text(
        (x_draw, y_draw),
        text,
        font=font,
        fill=final_text_color,
        stroke_width=int(stroke_width),
        stroke_fill=final_stroke_color,
        # 'direction="rtl"' removed
    )
    
    # cv2.imshow("Rendered Text Image", np.array(img, dtype=np.uint8))  # Debugging line to show the rendered image
    # cv2.waitKey(0)  # Wait for a key press to close the window

    return img

def process_video_with_subtitles(
    video_path: Path,
    transcript_path: Path,
    output_path: Path,
    font: Path = DEFAULT_FONT_PATH, # Use a full path to an Arabic-friendly font
    font_size: int = 32,
    color: str = "white",
    bg_color: str = "rgba(0,0,0,0.5)",
    stroke_color: str = "black",
    stroke_width: float = 1.5,
    align: str = "center",
    position: str = "center",
    # Add options for PIL text rendering defaults
    text_color_hex: str = "#FFFFFF", # Default white
    stroke_color_hex: str = "#000000", # Default black
    # Use hex for text/stroke colors for PIL consistency
    min_display_duration_s: float = 0 # New parameter for minimum display duration
):
    """
    Process video with Quranic text overlays using timestamp data from transcript.
    

    Args:
        video_path: Path to input video file
        transcript_path: Path to JSON transcript with timestamps
        output_path: Path to save output video
        font: Path to the font file (e.g., .ttf)
        font_size: Font size in pixels
        color: Not directly used for PIL text color, but can be for other elements if needed.
        bg_color: Background color with opacity (e.g., 'rgba(0,0,0,0.5)').
        stroke_color: Not directly used for PIL stroke color, use stroke_color_hex.
        stroke_width: Stroke width for PIL text.
        align: Text alignment ('center', 'east', 'west'). 'center' is most reliably implemented.
        position: Text position ('bottom', 'top').
        text_color_hex: Hex code for the text color (e.g., "#FFFFFF").
        stroke_color_hex: Hex code for the stroke color (e.g., "#000000").
        min_display_duration_s: Minimum duration for a subtitle clip in seconds.
    """
    # Load transcript data
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    
    # Load video
    video = VideoFileClip(str(video_path))
    
    # Process each ayah's word timestamps
    subtitles = []
    log.info("Processing subtitles for video...")
    
    all_words = []
    for ayah in transcript['ayah_data']:
        for word in ayah['word_timestamps']:
            if word['start_time'] is not None and word['end_time'] is not None:
                all_words.append({
                    'word_quranic': word['word_quranic'],
                    'start_time': word['start_time'],
                    'end_time': word['end_time'],
                    'surah': ayah['surah'],
                    'ayah_number': ayah['ayah_number']
                })

    num_words = len(all_words)
    word_idx = 0

    while word_idx < num_words:
        current_word_group_text = []
        current_group_start_time = all_words[word_idx]['start_time']
        current_group_end_time = all_words[word_idx]['end_time']
        
        group_accumulator_idx = word_idx
        
        while group_accumulator_idx < num_words:
            word = all_words[group_accumulator_idx]
            current_word_group_text.append(word['word_quranic'])
            current_group_end_time = word['end_time'] # Always extends to the latest word in the group

            current_group_actual_duration = current_group_end_time - current_group_start_time
            
            # Decide if we should render this group
            is_last_word = (group_accumulator_idx == num_words - 1)
            
            # If the group's natural duration meets the minimum OR it's the last word overall:
            if current_group_actual_duration >= min_display_duration_s or is_last_word:
                
                # Determine the effective end time for the clip based on min_display_duration_s
                # and the start time of the next actual word (to avoid overlap)

                suggested_clip_end = max(current_group_end_time, current_group_start_time + min_display_duration_s)
                
                next_word_start_time = float('inf') # Initialize with a very large number
                if group_accumulator_idx + 1 < num_words:
                    next_word_start_time = all_words[group_accumulator_idx + 1]['start_time']

                # The actual clip will end either at its suggested minimum duration end,
                # or just before the next word starts, whichever is earlier.
                clip_end_time = min(suggested_clip_end, next_word_start_time)

                # Ensure duration is not negative. If next_word_start_time is less than current_group_start_time, it's an issue.
                # (This shouldn't happen with sorted timestamps, but as a safeguard)
                clip_duration = max(0.0, clip_end_time - current_group_start_time)

                # Prepare Arabic text for the combined group
                combined_arabic_text = " ".join(current_word_group_text)
                bidi_text_group = get_display(arabic_reshaper.reshape(combined_arabic_text))
                
                log.debug(f"  Rendering group: '{bidi_text_group}' from {current_group_start_time:.2f} to {clip_end_time:.2f} (duration {clip_duration:.2f}s)")

                # --- Create text image using PIL ---
                text_image_pil = render_text_to_image(
                    text=bidi_text_group,
                    font_path=font,
                    font_size=font_size,
                    text_color_hex=text_color_hex,
                    stroke_color_hex=stroke_color_hex,
                    stroke_width=stroke_width
                )
                
                log.debug(f"  Rendered PIL Image size: {text_image_pil.size}")

                # Convert PIL Image to MoviePy ImageClip
                txt_clip_np = np.array(text_image_pil)
                txt_clip = ImageClip(txt_clip_np)
                
                log.debug(f"  MoviePy txt_clip dimensions: W={txt_clip.w}, H={txt_clip.h}, Duration={txt_clip.duration}s (before setting)")

                # Set position and timing for the group clip - using the user's updated composition
                bg_rgb   = parse_rgba_to_tuple(bg_color)[:3]
                bg_alpha = parse_rgba_to_tuple(bg_color)[3] / 255.0

                bg_w = txt_clip.w + 20
                bg_h = txt_clip.h + 10
                background_clip = (
                    ColorClip(size=(bg_w, bg_h), color=bg_rgb)
                        .with_opacity(bg_alpha)
                        .with_duration(clip_duration) # Use calculated clip_duration
                )
                
                # Align txt_clip in the center of its own panel
                txt_position_in_panel = ('center', 'center')

                panel_clip = CompositeVideoClip(
                    [
                        background_clip.with_position(txt_position_in_panel),
                        txt_clip.with_position(txt_position_in_panel)
                    ],
                    size=(bg_w, bg_h)
                )

                # Composite the text clip *over* the background clip
                bg_and_text_clip = (
                    panel_clip
                        .with_start(current_group_start_time)
                        .with_duration(clip_duration) # Use calculated clip_duration
                        .with_position(position)
                )
                
                log.debug(f"  Composite clip created with text '{bidi_text_group}' at position {position} "
                            f"from {current_group_start_time:.2f}s to {clip_end_time:.2f}s, size: {bg_and_text_clip.size}")
                
                subtitles.append(bg_and_text_clip)

                log.debug(f"  Group composite clip added. Total subtitles: {len(subtitles)}")

                # Move primary index past the words just processed
                word_idx = group_accumulator_idx + 1
                break # Exit inner loop, start new group with next word_idx
            
            # If not yet met criteria, accumulate more words
            group_accumulator_idx += 1
        else: # This else block executes if inner while loop completes without 'break'
            # This means group_accumulator_idx reached num_words, but the group's duration criteria was never met
            # This scenario should ideally not be reached if the last_word condition is correctly handled,
            # but as a fallback, ensure word_idx advances.
            word_idx = group_accumulator_idx # Advance word_idx to prevent infinite loop
    
    # Composite all clips
    final = CompositeVideoClip([video] + subtitles)
    
    # Write output
    final.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        threads=4,
        fps=video.fps
    )
    
    # Clean up
    video.close()
    final.close()
    
    log.info("Video processing complete.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add Quranic text overlays to video using timestamp data")
    parser.add_argument("video_file", type=Path, help="Input video file path")
    parser.add_argument("transcript_file", type=Path, help="JSON transcript file with timestamps")
    parser.add_argument("--output_file", type=Path, help="Output video file path", default=None)
    parser.add_argument("--min_display_duration_s", type=float, default=0.0,
                        help="Minimum duration (in seconds) for each text segment. Words will be grouped if their combined duration is less than this.")
    
    args = parser.parse_args()
    
    if not args.output_file:
        args.output_file = args.video_file.parent / f"{args.video_file.stem}_with_text{args.video_file.suffix}"
    
    process_video_with_subtitles(
        video_path=args.video_file,
        transcript_path=args.transcript_file,
        output_path=args.output_file,
        min_display_duration_s=args.min_display_duration_s
    )