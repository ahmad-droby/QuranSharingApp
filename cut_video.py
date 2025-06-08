import subprocess

input_video_path = "transcribe_quran/input1.mp4"
output_short_video_path = "transcribe_quran/input1_short.mp4"

# Define the start and end time (in seconds) for the shorter clip
# This example cuts the first 30 seconds of the video
start_time = 0
end_time = 30 # Adjust this to your desired length

def format_time(seconds):
    """Formats seconds into hh:mm:ss string."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02.0f}"

try:
    print(f"Attempting to cut video from {input_video_path} using ffmpeg...")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Error: FFmpeg is not found. Please install FFmpeg and add it to your system's PATH.")
        print("You can download it from https://ffmpeg.org/download.html")
        exit(1)

    command = [
        "ffmpeg",
        "-i", input_video_path,
        "-ss", format_time(start_time),
        "-to", format_time(end_time),
        "-c", "copy",  # Copy streams without re-encoding for speed (may cause issues with exact cuts)
        output_short_video_path
    ]
    
    # For more precise cutting, re-encode:
    # command = [
    #    "ffmpeg",
    #    "-i", input_video_path,
    #    "-ss", format_time(start_time),
    #    "-to", format_time(end_time),
    #    "-c:v", "libx264", "-preset", "ultrafast",  # Video codec + preset for speed
    #    "-c:a", "aac",                              # Audio codec
    #    output_short_video_path
    # ]

    print(f"Executing command: {' '.join(command)}")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    
    print("Video cutting complete!")
    print("FFmpeg stdout:\n", result.stdout)
    print("FFmpeg stderr:\n", result.stderr)

except subprocess.CalledProcessError as e:
    print(f"FFmpeg command failed with error code {e.returncode}")
    print("FFmpeg stdout:\n", e.stdout)
    print("FFmpeg stderr:\n", e.stderr)
    print(f"Please check your FFmpeg installation and the input video file.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")