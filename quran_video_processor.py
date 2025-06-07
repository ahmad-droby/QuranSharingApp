import json
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import arabic_reshaper
from bidi.algorithm import get_display

def process_video_with_subtitles(
    video_path: Path,
    transcript_path: Path,
    output_path: Path,
    font: str = "Arial",
    font_size: int = 48,
    color: str = "white",
    bg_color: str = "rgba(0,0,0,0.5)",
    stroke_color: str = "black",
    stroke_width: float = 1.5,
    align: str = "center",
    position: str = "bottom"
):
    """
    Process video with Quranic text overlays using timestamp data from transcript.
    
    Args:
        video_path: Path to input video file
        transcript_path: Path to JSON transcript with timestamps
        output_path: Path to save output video
        font: Font family for text
        font_size: Font size in pixels
        color: Text color
        bg_color: Background color with opacity
        stroke_color: Text stroke color
        stroke_width: Stroke width
        align: Text alignment ('center', 'east', 'west')
        position: Text position ('bottom', 'top')
    """
    # Load transcript data
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    
    # Load video
    video = VideoFileClip(str(video_path))
    
    # Process each ayah's word timestamps
    subtitles = []
    for ayah in transcript['ayah_data']:
        for word in ayah['word_timestamps']:
            if word['start_time'] and word['end_time']:
                # Prepare Arabic text with proper shaping and direction
                arabic_text = arabic_reshaper.reshape(word['word_quranic'])
                bidi_text = get_display(arabic_text)
                
                # Create styled text clip
                txt_clip = TextClip(
                    bidi_text,
                    font=font,
                    fontsize=font_size,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    align=align,
                    method='caption',
                    size=(video.w * 0.9, None)  # 90% of video width
                ).set_position(position).set_start(word['start_time']).set_end(word['end_time'])
                
                # Add semi-transparent background
                bg_clip = txt_clip.on_color(
                    size=(txt_clip.w + 20, txt_clip.h + 10),
                    color=(0,0,0),
                    pos=align,
                    col_opacity=0.5
                )
                
                subtitles.append(bg_clip)
    
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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add Quranic text overlays to video using timestamp data")
    parser.add_argument("video_file", type=Path, help="Input video file path")
    parser.add_argument("transcript_file", type=Path, help="JSON transcript file with timestamps")
    parser.add_argument("--output_file", type=Path, help="Output video file path", default=None)
    
    args = parser.parse_args()
    
    if not args.output_file:
        args.output_file = args.video_file.parent / f"{args.video_file.stem}_with_text{args.video_file.suffix}"
    
    process_video_with_subtitles(
        video_path=args.video_file,
        transcript_path=args.transcript_file,
        output_path=args.output_file
    )