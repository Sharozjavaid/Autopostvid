#!/usr/bin/env python3
"""
Simple test for philosophy video generation
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_basic_generation():
    """Test basic components"""
    
    print("🧪 Testing Philosophy Video Components")
    print("=" * 50)
    
    # Test voice generation first
    print("\n🎤 Testing Voice Generation...")
    try:
        from voice_generator import VoiceGenerator
        voice_gen = VoiceGenerator()
        
        test_script = """
        You sit in darkness, believing shadows on the wall are reality. 
        But what if everything you know is just an illusion? 
        This profound question drives Plato's famous Cave Allegory.
        What would you do if you discovered your entire world was fake?
        Explore more philosophical mysteries in our app.
        """
        
        audio_file = voice_gen.generate_voiceover(test_script.strip(), filename="test_plato.mp3")
        if audio_file:
            print(f"✅ Voice generation successful: {audio_file}")
        else:
            print("❌ Voice generation failed")
            
    except Exception as e:
        print(f"❌ Voice test error: {e}")
    
    # Test image generation (placeholder)
    print("\n🎨 Testing Image Generation...")
    try:
        from image_generator import ImageGenerator
        img_gen = ImageGenerator()
        
        test_scene = {
            'scene_number': 1,
            'text': 'Prisoners chained in a dark cave watching shadows',
            'visual_description': 'Dark cave with figures chained, watching shadows dance on stone wall, dramatic lighting',
            'key_concept': 'illusion of reality'
        }
        
        image_path = img_gen.generate_philosophy_image(test_scene, "Platos_Cave_Test")
        if image_path and os.path.exists(image_path):
            print(f"✅ Image generation successful: {image_path}")
        else:
            print("❌ Image generation failed")
            
    except Exception as e:
        print(f"❌ Image test error: {e}")
    
    # Test video assembly
    print("\n🎬 Testing Video Assembly...")
    try:
        from video_assembler import VideoAssembler
        
        # Create test scenes data
        test_scenes = [
            {"scene_number": 1, "duration": 8, "text": "You sit chained in darkness...", "key_concept": "Illusion"},
            {"scene_number": 2, "duration": 8, "text": "Shadows dance on the wall...", "key_concept": "Reality"},
            {"scene_number": 3, "duration": 7, "text": "What if you could break free?", "key_concept": "Freedom"}
        ]
        
        assembler = VideoAssembler()
        print(f"✅ Video assembler initialized successfully")
        
        # If we have audio and images, try to assemble
        if 'audio_file' in locals() and 'image_path' in locals():
            image_paths = [image_path, image_path, image_path]  # Use same image for test
            
            video_path = assembler.create_philosophy_video(
                test_scenes, audio_file, image_paths, "Plato_Cave_Test"
            )
            
            if video_path and os.path.exists(video_path):
                print(f"✅ Video assembly successful: {video_path}")
                
                # Optimize for TikTok
                optimized = assembler.optimize_for_tiktok(video_path)
                print(f"✅ TikTok optimization complete: {optimized}")
            else:
                print("❌ Video assembly failed")
        else:
            print("⚠️  Skipping video assembly (missing audio or images)")
            
    except Exception as e:
        print(f"❌ Video test error: {e}")
    
    print("\n🎯 Test Complete!")
    print("Check the generated_* folders for output files")

if __name__ == "__main__":
    test_basic_generation()