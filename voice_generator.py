from elevenlabs import ElevenLabs
import os
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
    
    def get_available_voices(self):
        """Get list of available voices (placeholder for now)"""
        # This would query ElevenLabs API for available voices
        # For now, return common voice options
        return [
            {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Philosophy Narrator (Default)", "description": "User preferred voice"},
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