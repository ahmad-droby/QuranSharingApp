import argparse
import subprocess
from pathlib import Path
import sys

def run_transcription(video_path: Path, output_dir: Path) -> Path:
    """Runs transcribe_quran.py to generate a JSON transcript."""
    # transcribe_quran.py expects a single output_file path, not separate dir and name.
    # It also handles surah/ayah hints as separate arguments.
    
    transcript_output_path = output_dir / f"output_transcript_{video_path.stem}.json"

    # Assuming transcribe_quran.py is in the 'transcribe_quran' directory relative to the current script
    transcribe_script_path = Path("transcribe_quran/transcribe_quran.py")
    
    command = [
        sys.executable, str(transcribe_script_path),
        str(video_path),
        "--output_file", str(transcript_output_path), # Pass the full output file path
        # Default hints for testing based on previous runs
        "--surah_hint", "23",
        "--start_ayah_hint", "1",
        "--end_ayah_hint", "7"
    ]
    
    print(f"Running transcription command: {' '.join(str(c) for c in command)}") # Convert all command parts to string for printing
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Transcription successful. Transcript saved to: {transcript_output_path}")
        return transcript_output_path
    except subprocess.CalledProcessError as e:
        print(f"Transcription failed with error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: transcribe_quran.py not found at {transcribe_script_path}. Ensure the path is correct.")
        sys.exit(1)

def run_video_processor(video_path: Path, transcript_path: Path, output_path: Path, min_display_duration_s: float):
    """Runs quran_video_processor.py to overlay text on video."""
    
    processor_script_path = Path("quran_video_processor.py")
    
    command = [
        sys.executable, str(processor_script_path),
        str(video_path),
        str(transcript_path),
        "--output_file", str(output_path),
        "--min_display_duration_s", str(min_display_duration_s)
    ]

    print(f"Running video processing command: {' '.join(str(c) for c in command)}") # Convert all command parts to string for printing
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Video processing successful. Output saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Video processing failed with error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: quran_video_processor.py not found at {processor_script_path}. Ensure the path is correct.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate Quran video with subtitles from an audio/video input.")
    parser.add_argument("input_video", type=Path, help="Path to the input video file.")
    parser.add_argument("--output_file", type=Path, default=None,
                        help="Path for the output video file. Defaults to input_video_stem_with_text.mp4 in the same directory.")
    parser.add_argument("--output_dir", type=Path, default=Path("transcribe_quran/output_cli"),
                        help="Directory to save transcription outputs (JSON). Defaults to 'transcribe_quran/output_cli'.")
    parser.add_argument("--min_display_duration_s", type=float, default=2.0,
                        help="Minimum duration (in seconds) for each text segment in the video. Words will be grouped if their combined duration is less than this.")
    
    args = parser.parse_args()

    # Ensure output directory exists for transcript
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.output_file:
        args.output_file = args.input_video.parent / f"{args.input_video.stem}_with_text.mp4"

    # Step 1: Run transcription
    transcript_path = run_transcription(args.input_video, args.output_dir)

    # Step 2: Run video processing
    run_video_processor(args.input_video, transcript_path, args.output_file, args.min_display_duration_s)

    print("\nFull Quran video generation process completed.")

if __name__ == "__main__":
    main()