from elevenlabs import ElevenLabs
import os
import json
import base64
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class VoiceGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            print("Warning: ElevenLabs API key not found. Please set ELEVENLABS_API_KEY in .env file")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=self.api_key)
        
        self.output_dir = "generated_audio"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_voiceover(self, script: str, voice_id: str = None, filename: str = None) -> str:
        """Generate voiceover using ElevenLabs API"""
        
        if not self.client:
            print("Cannot generate audio without API key")
            return None
        
        try:
            # Use default voice if none specified
            voice_to_use = voice_id if voice_id else "onwK4e9ZLuTAKqWW03F9"  # Updated voice ID
            
            # Generate audio
            audio = self.client.text_to_speech.convert(
                voice_id=voice_to_use,
                text=script,
                model_id="eleven_turbo_v2_5"  # Updated model for free tier
            )
            
            # Save audio file
            if not filename:
                filename = f"{self.output_dir}/philosophy_narration.mp3"
            else:
                filename = f"{self.output_dir}/{filename}"
            
            with open(filename, 'wb') as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
            
            print(f"Audio generated successfully: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error generating voiceover: {e}")
            return None
    
    def generate_voiceover_with_timestamps(
        self, 
        script: str, 
        scenes: List[Dict],
        voice_id: str = None, 
        filename: str = None
    ) -> Optional[Dict]:
        """
        Generate voiceover with word-level timestamps for scene synchronization.
        
        Uses ElevenLabs /with-timestamps endpoint to get exact timing data.
        
        Args:
            script: Full narration text
            scenes: List of scene dicts with 'text' field for each scene
            voice_id: ElevenLabs voice ID (optional)
            filename: Output filename (optional)
            
        Returns:
            {
                "audio_path": "path/to/file.mp3",
                "total_duration": 62.5,
                "word_timestamps": [
                    {"word": "These", "start": 0.0, "end": 0.3},
                    ...
                ],
                "scene_timings": [
                    {"scene_number": 1, "start": 0.0, "end": 5.2, "duration": 5.2},
                    ...
                ]
            }
        """
        if not self.api_key:
            print("Cannot generate audio without API key")
            return None
        
        try:
            voice_to_use = voice_id if voice_id else "onwK4e9ZLuTAKqWW03F9"
            
            # Use the with-timestamps endpoint via REST API
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_to_use}/with-timestamps"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": script,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            print("Generating audio with timestamps...")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract audio (base64 encoded)
            audio_base64 = result.get("audio_base64", "")
            if not audio_base64:
                print("Error: No audio data in response")
                return None
            
            # Decode and save audio
            audio_bytes = base64.b64decode(audio_base64)
            
            if not filename:
                filename = f"{self.output_dir}/narration_with_timestamps.mp3"
            else:
                if not filename.startswith(self.output_dir):
                    filename = f"{self.output_dir}/{filename}"
            
            with open(filename, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"Audio saved: {filename}")
            
            # Extract alignment data
            alignment = result.get("alignment", {})
            characters = alignment.get("characters", [])
            char_starts = alignment.get("character_start_times_seconds", [])
            char_ends = alignment.get("character_end_times_seconds", [])
            
            # Convert character-level to word-level timestamps
            word_timestamps = self._chars_to_words(characters, char_starts, char_ends)
            
            # Calculate total duration
            total_duration = char_ends[-1] if char_ends else 0
            
            # Map words to scenes to get scene timings
            scene_timings = self._calculate_scene_timings(scenes, word_timestamps, script)
            
            print(f"Total audio duration: {total_duration:.2f}s")
            print(f"Scenes mapped: {len(scene_timings)}")
            
            return {
                "audio_path": filename,
                "total_duration": total_duration,
                "word_timestamps": word_timestamps,
                "scene_timings": scene_timings
            }
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error generating audio with timestamps: {e}")
            print(f"Response: {e.response.text if e.response else 'No response'}")
            return None
        except Exception as e:
            print(f"Error generating voiceover with timestamps: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _chars_to_words(
        self, 
        characters: List[str], 
        char_starts: List[float], 
        char_ends: List[float]
    ) -> List[Dict]:
        """Convert character-level timestamps to word-level timestamps."""
        words = []
        current_word = ""
        word_start = None
        word_end = None
        
        for i, char in enumerate(characters):
            if char == " " or char == "\n":
                # End of word
                if current_word:
                    words.append({
                        "word": current_word,
                        "start": word_start,
                        "end": word_end
                    })
                current_word = ""
                word_start = None
                word_end = None
            else:
                # Continue building word
                if word_start is None:
                    word_start = char_starts[i] if i < len(char_starts) else 0
                word_end = char_ends[i] if i < len(char_ends) else word_start
                current_word += char
        
        # Don't forget last word
        if current_word:
            words.append({
                "word": current_word,
                "start": word_start,
                "end": word_end
            })
        
        return words
    
    def _calculate_scene_timings(
        self, 
        scenes: List[Dict], 
        word_timestamps: List[Dict],
        full_script: str
    ) -> List[Dict]:
        """
        Map word timestamps to scenes to calculate scene start/end times.
        
        Matches scene text to the word timestamps to find boundaries.
        """
        scene_timings = []
        word_index = 0
        
        for scene in scenes:
            scene_text = scene.get('text', '')
            scene_words = scene_text.split()
            scene_number = scene.get('scene_number', len(scene_timings) + 1)
            
            if not scene_words:
                continue
            
            # Find the start of this scene's words in the timestamp list
            scene_start = None
            scene_end = None
            words_matched = 0
            
            # Look for matching words starting from current position
            start_search_idx = word_index
            
            for i in range(start_search_idx, len(word_timestamps)):
                ts_word = word_timestamps[i]['word'].strip('.,!?:;"\'-').lower()
                
                if words_matched < len(scene_words):
                    target_word = scene_words[words_matched].strip('.,!?:;"\'-').lower()
                    
                    if ts_word == target_word or ts_word in target_word or target_word in ts_word:
                        if scene_start is None:
                            scene_start = word_timestamps[i]['start']
                        scene_end = word_timestamps[i]['end']
                        words_matched += 1
                        word_index = i + 1
                    elif words_matched > 0:
                        # Partial match broken, reset
                        words_matched = 0
                        scene_start = None
            
            # If we found timing for this scene
            if scene_start is not None and scene_end is not None:
                duration = scene_end - scene_start
                scene_timings.append({
                    "scene_number": scene_number,
                    "start": round(scene_start, 3),
                    "end": round(scene_end, 3),
                    "duration": round(duration, 3),
                    "word_count": len(scene_words),
                    "text_preview": scene_text[:50] + "..." if len(scene_text) > 50 else scene_text
                })
            else:
                # Fallback: estimate based on word count
                estimated_duration = len(scene_words) / 2.5  # ~2.5 words per second
                prev_end = scene_timings[-1]['end'] if scene_timings else 0
                
                scene_timings.append({
                    "scene_number": scene_number,
                    "start": round(prev_end, 3),
                    "end": round(prev_end + estimated_duration, 3),
                    "duration": round(estimated_duration, 3),
                    "word_count": len(scene_words),
                    "text_preview": scene_text[:50] + "..." if len(scene_text) > 50 else scene_text,
                    "estimated": True  # Flag that this was estimated
                })
        
        return scene_timings
    
    def get_available_voices(self):
        """Get list of available voices (placeholder for now)"""
        # This would query ElevenLabs API for available voices
        # For now, return common voice options
        return [
            {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Philosophy Narrator (Default)", "description": "User preferred voice"},
            {"id": "UmQN7jS1Ee8B1czsUtQh", "name": "Documentary Narrator", "description": "Cinematic documentary style voice"},
            {"id": "PWhh1WzgMTAFViXFirRr", "name": "🎙️ Voice Library 3", "description": "ElevenLabs community voice - test option"},
            {"id": "BiUApjQkV8SiOpzKnh18", "name": "🎙️ Voice Library 1", "description": "ElevenLabs community voice - test option"},
            {"id": "5Xx8kcjjamcaKohQT5wv", "name": "🎙️ Voice Library 2", "description": "ElevenLabs community voice - test option"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "Deep, authoritative male voice"},
            {"id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "description": "Clear, professional female voice"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "description": "Warm, narrative male voice"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "description": "Rich, mature male voice"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "description": "Smooth, engaging female voice"},
            {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "description": "Young, energetic female voice"},
            {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "description": "Friendly, conversational male voice"},
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Calm, soothing female voice"},
            {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "description": "Clear, articulate male voice"}
        ]
    
    def test_voice_generation(self, test_text: str = None):
        """Test voice generation with sample text"""
        if not test_text:
            test_text = """
            You sit in darkness, believing shadows on the wall are reality. 
            But what if everything you know is just an illusion? 
            This is the profound question Plato asked in his famous Cave Allegory.
            """
        
        print("Testing voice generation...")
        audio_file = self.generate_voiceover(test_text, filename="test_voice.mp3")
        
        if audio_file:
            print(f"Test audio generated: {audio_file}")
            return audio_file
        else:
            print("Voice generation test failed")
            return None

# Example usage
if __name__ == "__main__":
    voice_gen = VoiceGenerator()
    
    # List available voices
    voices = voice_gen.get_available_voices()
    print("Available voices:")
    for voice in voices:
        print(f"- {voice['name']}: {voice['description']}")
    
    # Test generation
    voice_gen.test_voice_generation()