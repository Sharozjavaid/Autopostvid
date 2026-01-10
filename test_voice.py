#!/usr/bin/env python3
"""
Test ElevenLabs voice generation
"""

from voice_generator import VoiceGenerator
import os

def test_voice():
    print("🎤 Testing ElevenLabs Voice Generation")
    print("=" * 40)
    
    # Test script for Plato's Cave
    test_script = """
    You sit in darkness, believing shadows on the wall are reality.
    These dancing forms seem so real, so meaningful.
    But what if everything you know is just an illusion?
    This profound question drives Plato's famous Cave Allegory.
    What would you do if you discovered your entire world was fake?
    Explore more philosophical mysteries in our app.
    """
    
    try:
        voice_gen = VoiceGenerator()
        print("✅ Voice generator initialized")
        
        # Test voice generation
        print("🎙️  Generating voice for Plato's Cave story...")
        audio_file = voice_gen.generate_voiceover(
            test_script.strip(), 
            filename="plato_cave_voice_test.mp3"
        )
        
        if audio_file and os.path.exists(audio_file):
            print(f"✅ SUCCESS! Voice generated: {audio_file}")
            file_size = os.path.getsize(audio_file)
            print(f"📁 File size: {file_size} bytes")
            
            # Test with different voice
            print("\n🎭 Testing with Rachel voice...")
            audio_file2 = voice_gen.generate_voiceover(
                "This is a test with Rachel's calm, soothing voice.",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                filename="rachel_test.mp3"
            )
            
            if audio_file2 and os.path.exists(audio_file2):
                print(f"✅ Rachel voice test successful: {audio_file2}")
            
            return True
            
        else:
            print("❌ Voice generation failed - no file created")
            return False
            
    except Exception as e:
        print(f"❌ Voice generation error: {e}")
        return False

if __name__ == "__main__":
    success = test_voice()
    if success:
        print("\n🎉 Voice generation working! Ready for full video creation.")
    else:
        print("\n⚠️  Voice generation needs troubleshooting.")