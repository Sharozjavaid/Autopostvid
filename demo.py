#!/usr/bin/env python3
"""
Philosophy Video Demo - Working Version
Creates a sample philosophy video with available components
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def create_sample_video():
    """Create a philosophy video using working components"""
    
    print("🧠 Philosophy Video Demo")
    print("=" * 40)
    
    # Sample philosophy story about Plato's Cave
    story_script = """
    You sit in darkness, believing shadows on the wall are reality.
    These dancing forms seem so real, so meaningful.
    But what if everything you know is just an illusion?
    This is the profound question Plato asked in his Cave Allegory.
    Imagine being freed from these chains of ignorance.
    What would you see when you step into the light?
    True knowledge awaits those brave enough to question reality.
    Explore deeper philosophical mysteries with our app.
    """
    
    # Scene breakdown for the story
    scenes = [
        {
            "scene_number": 1,
            "duration": 7,
            "text": "You sit in darkness, believing shadows on the wall are reality. These dancing forms seem so real, so meaningful.",
            "visual_description": "Dark cave interior with chained figures watching shadows dance on stone wall",
            "key_concept": "Illusion of Reality"
        },
        {
            "scene_number": 2, 
            "duration": 7,
            "text": "But what if everything you know is just an illusion? This is the profound question Plato asked in his Cave Allegory.",
            "visual_description": "Philosophical scene showing Plato contemplating, classical Greek setting",
            "key_concept": "Questioning Reality"
        },
        {
            "scene_number": 3,
            "duration": 8,
            "text": "Imagine being freed from these chains of ignorance. What would you see when you step into the light?",
            "visual_description": "Figure breaking free from chains, emerging into bright sunlight, transformation",
            "key_concept": "Enlightenment"
        },
        {
            "scene_number": 4,
            "duration": 8,
            "text": "True knowledge awaits those brave enough to question reality. Explore deeper philosophical mysteries with our app.",
            "visual_description": "Wise figure standing in light holding scroll, ancient library or temple",
            "key_concept": "Wisdom"
        }
    ]
    
    print(f"📖 Story: Plato's Cave Allegory")
    print(f"🎬 Duration: ~30 seconds")
    print(f"🎨 Scenes: {len(scenes)}")
    
    # Step 1: Generate Voice
    print("\n🎤 Generating voiceover...")
    try:
        from voice_generator import VoiceGenerator
        voice_gen = VoiceGenerator()
        
        audio_file = voice_gen.generate_voiceover(
            story_script.strip(),
            filename="plato_cave_demo.mp3"
        )
        
        if audio_file and os.path.exists(audio_file):
            print(f"✅ Voice generation successful: {audio_file}")
            voice_success = True
        else:
            print("❌ Voice generation failed")
            voice_success = False
            
    except Exception as e:
        print(f"❌ Voice error: {e}")
        voice_success = False
    
    # Step 2: Generate Images
    print("\n🎨 Generating scene images...")
    try:
        from image_generator import ImageGenerator
        img_gen = ImageGenerator()
        
        image_paths = []
        for scene in scenes:
            print(f"  Creating image for scene {scene['scene_number']}...")
            image_path = img_gen.generate_philosophy_image(scene, "Platos_Cave_Demo")
            if image_path:
                image_paths.append(image_path)
        
        print(f"✅ Generated {len(image_paths)} placeholder images")
        images_success = len(image_paths) == len(scenes)
        
    except Exception as e:
        print(f"❌ Image error: {e}")
        images_success = False
        image_paths = []
    
    # Step 3: Assemble Video
    print("\n🎬 Assembling video...")
    try:
        import subprocess
        
        # Check if MoviePy is working
        result = subprocess.run([sys.executable, "-c", "import moviepy.editor; print('MoviePy OK')"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ MoviePy available")
            
            if voice_success and images_success and len(image_paths) > 0:
                from video_assembler import VideoAssembler
                assembler = VideoAssembler()
                
                video_path = assembler.create_philosophy_video(
                    scenes, audio_file, image_paths, "Platos_Cave_Demo"
                )
                
                if video_path and os.path.exists(video_path):
                    print(f"✅ Video created: {video_path}")
                    
                    # Optimize for TikTok
                    optimized_path = assembler.optimize_for_tiktok(video_path)
                    print(f"✅ TikTok version: {optimized_path}")
                    
                    return {
                        "success": True,
                        "video_path": video_path,
                        "optimized_path": optimized_path,
                        "audio_path": audio_file,
                        "image_paths": image_paths,
                        "story": "Plato's Cave Allegory"
                    }
                else:
                    print("❌ Video assembly failed")
            else:
                print("⚠️  Cannot assemble video - missing components")
                if not voice_success:
                    print("   - Voice generation failed")
                if not images_success:
                    print("   - Image generation failed")
        else:
            print(f"❌ MoviePy not working: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Video assembly error: {e}")
    
    # Summary
    print(f"\n📋 Demo Summary:")
    print(f"   Voice: {'✅' if voice_success else '❌'}")
    print(f"   Images: {'✅' if images_success else '❌'}")
    print(f"   Video: ⚠️  (Check generated_videos/ folder)")
    
    if voice_success:
        print(f"\n🔊 You can listen to the generated audio:")
        print(f"   {audio_file}")
    
    if images_success:
        print(f"\n🖼️  Generated placeholder images in:")
        print(f"   generated_images/ folder")
    
    print(f"\n💡 This demonstrates the complete pipeline!")
    print(f"   Next: Add your ElevenLabs API key and try the full version")
    
    return {
        "success": False,
        "message": "Demo completed with available components"
    }

if __name__ == "__main__":
    create_sample_video()