import os
import json
import re
import requests
from pydub import AudioSegment
import moviepy as mp
from typing import List, Dict, Any, Optional, Tuple
import whisper

class QuranVideoGenerator:
    def __init__(self, video_path: str, output_path: str):
        self.video_path = video_path
        self.output_path = output_path
        self.video = mp.VideoFileClip(video_path)
        
    def add_quran_text(self, quran_text: List[Dict[str, Any]]):
        # Add text to video
        final_video = self.video.copy()
        
        for i, verse in enumerate(quran_text):
            start_time = verse['start_time']
            end_time = verse['end_time']
            text = verse['text']
            
            # Add text overlay
            txt_clip = mp.TextClip(text, fontsize=70, color='white').set_position('center').set_duration(end_time - start_time)
            txt_clip = txt_clip.set_start(start_time)
            
            final_video = mp.CompositeVideoClip([final_video, txt_clip])
            
        final_video.write_videofile(self.output_path)
        
    def extract_audio(self) -> str:
        # Extract audio from video
        audio_path = os.path.splitext(self.video_path)[0] + '_audio.mp3'
        audio = AudioSegment.from_file(self.video_path, format=os.path.splitext(self.video_path)[1])
        audio.export(audio_path, format='mp3')
        return audio_path

class QuranTranscriber:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        
    def transcribe(self) -> List[Dict[str, Any]]:
        # Initialize Whisper
        model = whisper.load_model("small")
        
        # Transcribe audio
        result = model.transcribe(self.audio_path, language="ar")
        
        # Process segments
        verses = []
        for segment in result["segments"]:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]
            
            # Convert seconds to moviepy time format (seconds + milliseconds)
            start_time_moviepy = int(start_time) + (start_time - int(start_time)) 
            end_time_moviepy = int(end_time) + (end_time - int(end_time))
            
            verses.append({
                'start_time': start_time_moviepy,
                'end_time': end_time_moviepy,
                'text': text
            })
            
        # Save transcription to file
        with open('transcription.json', 'w', encoding='utf-8') as f:
            json.dump(verses, f, indent=2, ensure_ascii=False)
            
        return verses

class QuranAPI:
    def __init__(self):
        self.verse_pattern = re.compile(r"(?:سورة|سورَة|سوره)\s*(\d+)[،,\s]+(?:آية|آيه|اية|آیة)\s*(\d+)")
        self.base_url = "https://api.quran.com/api/v4"
        
    def get_quran_text(self, surah: int, ayah: int) -> Dict[str, Any]:
        """Fetch Quran text with metadata"""
        try:
            response = requests.get(
                f"{self.base_url}/verses/by_key/{surah}:{ayah}",
                params={"language": "ar", "fields": "text_uthmani"}
            )
            response.raise_for_status()
            data = response.json()
            return {
                'text': data['verse']['text_uthmani'],
                'surah': surah,
                'ayah': ayah,
                'surah_name': self._get_surah_name(surah)
            }
        except Exception as e:
            print(f"Error fetching verse {surah}:{ayah}: {str(e)}")
            return None
            
    def _get_surah_name(self, surah_num: int) -> str:
        try:
            response = requests.get(f"{self.base_url}/chapters/{surah_num}")
            response.raise_for_status()
            return response.json()['chapter']['name_arabic']
        except Exception:
            return f"سورة {surah_num}"
            
    def detect_verse(self, text: str) -> Optional[Tuple[int, int]]:
        """Detect surah and ayah numbers from transcribed text"""
        match = self.verse_pattern.search(text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

# Example usage
if __name__ == "__main__":
    video_path = "input.mp4"
    output_path = "output.mp4"
    
    generator = QuranVideoGenerator(video_path, output_path)
    audio_path = generator.extract_audio()
    
    transcriber = QuranTranscriber(audio_path)
    transcription = transcriber.transcribe()
    
    # Match transcription with Quran text from API
    quran_api = QuranAPI()
    verses_with_text = []
    
    # Enhanced verse matching
    quran_api = QuranAPI()
    verses_with_text = []
    current_surah, current_ayah = 1, 1  # Default starting point
    
    for verse in transcription:
        # Try to detect verse numbers from transcription
        detected = quran_api.detect_verse(verse['text'])
        if detected:
            current_surah, current_ayah = detected
            
        # Get Quran text with metadata
        quran_verse = quran_api.get_quran_text(current_surah, current_ayah)
        if quran_verse:
            verses_with_text.append({
                'start_time': verse['start_time'],
                'end_time': verse['end_time'],
                'text': quran_verse['text'],
                'surah': quran_verse['surah'],
                'ayah': quran_verse['ayah'],
                'surah_name': quran_verse['surah_name']
            })
            current_ayah += 1  # Move to next ayah
        else:
            # Fallback to transcribed text if API fails
            verses_with_text.append({
                'start_time': verse['start_time'],
                'end_time': verse['end_time'],
                'text': verse['text'],
                'surah': current_surah,
                'ayah': current_ayah,
                'surah_name': f"سورة {current_surah}"
            })
    
    generator.add_quran_text(verses_with_text)