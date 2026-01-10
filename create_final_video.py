#!/usr/bin/env python3
"""
Create Final Philosophy Video
Assemble complete TikTok-ready video from all components
"""

import os
from moviepy.editor import *
from voice_generator import VoiceGenerator
from working_demo import create_placeholder_images

def create_complete_philosophy_video():
    """Create the final philosophy video with all components"""
    
    print("🎬 Creating Complete Philosophy Video")
    print("=" * 50)
    
    # Philosophy story for Plato's Cave
    story_script = """
    You sit in darkness, believing shadows on the wall are reality.
    These dancing forms seem so real, so meaningful.
    But what if everything you know is just an illusion?
    This profound question drives Plato's famous Cave Allegory.
    Imagine being freed from these chains of ignorance.
    What would you see when you step into the light?
    True knowledge awaits those brave enough to question reality.
    Explore deeper philosophical mysteries with our app.
    """
    
    scenes = [
        {"scene_number": 1, "duration": 7, "text": "You sit in darkness, believing shadows on the wall are reality. These dancing forms seem so real, so meaningful.", "key_concept": "Illusion"},
        {"scene_number": 2, "duration": 7, "text": "But what if everything you know is just an illusion? This profound question drives Plato's famous Cave Allegory.", "key_concept": "Questioning"}, 
        {"scene_number": 3, "duration": 8, "text": "Imagine being freed from these chains of ignorance. What would you see when you step into the light?", "key_concept": "Freedom"},
        {"scene_number": 4, "duration": 8, "text": "True knowledge awaits those brave enough to question reality. Explore deeper philosophical mysteries with our app.", "key_concept": "Wisdom"}
    ]
    
    print(f"📖 Story: Plato's Cave Allegory")
    print(f"🎬 Total Duration: {sum(s['duration'] for s in scenes)} seconds")
    
    # Step 1: Ensure we have images
    print(f"\n🎨 Checking/Creating Images...")
    expected_images = [
        "generated_images/plato_cave_scene_1.png",
        "generated_images/plato_cave_scene_2.png", 
        "generated_images/plato_cave_scene_3.png",
        "generated_images/plato_cave_scene_4.png"
    ]
    
    missing_images = [img for img in expected_images if not os.path.exists(img)]
    if missing_images:
        print("Creating missing images...")
        create_placeholder_images()
    
    # Verify all images exist
    image_paths = []
    for img_path in expected_images:
        if os.path.exists(img_path):
            image_paths.append(img_path)
            print(f"✅ Found: {os.path.basename(img_path)}")
        else:
            print(f"❌ Missing: {img_path}")
    
    if len(image_paths) != 4:
        print(f"Error: Need 4 images, found {len(image_paths)}")
        return None
    
    # Step 2: Generate/Check Audio
    print(f"\n🎤 Checking/Creating Audio...")
    audio_path = "generated_audio/plato_cave_final.mp3"
    
    if not os.path.exists(audio_path):
        print("Generating fresh voiceover...")
        voice_gen = VoiceGenerator()
        audio_path = voice_gen.generate_voiceover(
            story_script.strip(),
            filename="plato_cave_final.mp3"
        )
    
    if os.path.exists(audio_path):
        print(f"✅ Audio ready: {audio_path}")
    else:
        print(f"❌ Audio generation failed")
        return None
    
    # Step 3: Create Video
    print(f"\n🎬 Assembling TikTok Video...")
    try:
        # Load audio first to get duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        print(f"📻 Audio duration: {total_duration:.1f} seconds")
        
        # TikTok dimensions
        width, height = 1080, 1920
        
        # Create video clips from images
        video_clips = []
        current_time = 0
        
        for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
            # Calculate duration for this scene
            scene_duration = scene['duration']
            if i == len(scenes) - 1:  # Last scene gets remaining time
                scene_duration = total_duration - current_time
            
            print(f"Scene {i+1}: {scene_duration:.1f}s - {scene['key_concept']}")
            
            # Create image clip with motion
            img_clip = (ImageClip(image_path)
                       .set_duration(scene_duration)
                       .set_start(current_time)
                       .resize(height=height)
                       .set_position('center'))
            
            # Add subtle zoom effect for engagement
            img_clip = img_clip.resize(lambda t: 1 + 0.02 * (t / scene_duration))
            
            video_clips.append(img_clip)
            current_time += scene_duration
        
        print(f"✅ Created {len(video_clips)} video segments")
        
        # Combine all clips
        final_video = CompositeVideoClip(video_clips, size=(width, height))
        
        # Add audio
        final_video = final_video.set_audio(audio_clip)
        final_video = final_video.set_duration(total_duration)
        
        # Add fade effects
        final_video = final_video.fadeout(0.5).fadein(0.5)
        
        # Add key concept text overlays
        text_clips = []
        current_time = 0
        
        for scene in scenes:
            scene_duration = scene['duration']
            concept = scene['key_concept'].upper()
            
            # Create text overlay
            txt_clip = (TextClip(concept, 
                               fontsize=60, 
                               color='#FFD700',
                               font='Arial-Bold',
                               stroke_color='black',
                               stroke_width=3)
                       .set_position(('center', 0.15))  # Top of screen
                       .set_duration(2)  # Show for 2 seconds
                       .set_start(current_time + scene_duration - 2)  # Show at end of scene
                       .fadeout(0.5))
            
            text_clips.append(txt_clip)
            current_time += scene_duration
        
        # Add text overlays to video
        if text_clips:
            final_video = CompositeVideoClip([final_video] + text_clips)
        
        # Output path
        output_path = "generated_videos/plato_cave_philosophy_tiktok.mp4"
        os.makedirs("generated_videos", exist_ok=True)
        
        print(f"🎬 Rendering TikTok video...")
        print(f"   Resolution: {width}x{height}")
        print(f"   Duration: {total_duration:.1f} seconds")
        print(f"   Output: {output_path}")
        
        # Render with TikTok-optimized settings
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='medium',
            ffmpeg_params=['-crf', '23']  # Good quality
        )
        
        # Create optimized version
        optimized_path = "generated_videos/plato_cave_tiktok_optimized.mp4"
        
        print(f"📱 Creating TikTok-optimized version...")
        optimized_video = final_video.resize(height=1920).crop(width=1080, height=1920, x_center=final_video.w/2, y_center=final_video.h/2)
        
        optimized_video.write_videofile(
            optimized_path,
            fps=30,
            codec='libx264', 
            audio_codec='aac',
            bitrate="1000k",
            preset='fast'
        )
        
        # Clean up
        audio_clip.close()
        final_video.close()
        optimized_video.close()
        
        # Get file info
        if os.path.exists(optimized_path):
            file_size = os.path.getsize(optimized_path)
            print(f"\n🎉 SUCCESS! Philosophy Video Created!")
            print(f"📁 File: {optimized_path}")
            print(f"📊 Size: {file_size / 1024 / 1024:.1f} MB")
            print(f"⏱️  Duration: {total_duration:.1f} seconds")
            print(f"📱 Format: TikTok-ready (1080x1920)")
            
            return optimized_path
        
    except Exception as e:
        print(f"❌ Video creation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    print("🧠 Philosophy Video Generator - Final Production")
    print("=" * 60)
    
    video_path = create_complete_philosophy_video()
    
    if video_path:
        print(f"\n✨ YOUR PHILOSOPHY VIDEO IS READY!")
        print(f"🎬 File: {video_path}")
        print(f"📱 Ready to upload to TikTok/Instagram/YouTube Shorts!")
        
        print(f"\n🎯 Video Features:")
        print(f"   ✅ Engaging Plato's Cave Allegory story")
        print(f"   ✅ Professional AI narration") 
        print(f"   ✅ 4 classical philosophical images")
        print(f"   ✅ TikTok-optimized format (9:16)")
        print(f"   ✅ Philosophy app promotion")
        print(f"   ✅ Key concept overlays")
        print(f"   ✅ Smooth transitions and effects")
        
        print(f"\n🚀 This video will help promote your philosophy app!")
        
        return video_path
    else:
        print(f"\n❌ Video creation failed. Check the errors above.")
        return None

if __name__ == "__main__":
    result = main()