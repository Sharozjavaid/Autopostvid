from moviepy.editor import *
import os
from typing import List, Dict
import json

class VideoAssembler:
    def __init__(self):
        self.output_dir = "generated_videos"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # TikTok optimal settings
        self.width = 1080
        self.height = 1920
        self.fps = 30
    
    def create_philosophy_video(self, 
                              scenes: List[Dict], 
                              audio_path: str, 
                              image_paths: List[str],
                              story_title: str) -> str:
        """Assemble final video using Word-Count Alignment for better flow"""
        
        try:
            # Load the single continuous audio file
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            print(f"Audio duration: {total_duration} seconds")
            
            # Calculate total word count to determine proportions
            total_words = 0
            scene_word_counts = []
            
            for scene in scenes:
                text = scene.get('text', '')
                word_count = len(text.split())
                # Ensure at least 1 word to avoid division errors
                word_count = max(1, word_count)
                scene_word_counts.append(word_count)
                total_words += word_count
                
            print(f"Total words: {total_words}")
            
            # Create video clips with proportional duration
            video_clips = []
            
            for i, (scene, image_path, word_count) in enumerate(zip(scenes, image_paths, scene_word_counts)):
                if not os.path.exists(image_path):
                    print(f"Warning: Image not found: {image_path}")
                    continue
                
                # proportional duration
                proportion = word_count / total_words
                duration = total_duration * proportion
                
                # Create image clip
                # START TIME IS AUTOMATICALLY HANDLED BY CONCATENATE
                img_clip = (ImageClip(image_path)
                           .set_duration(duration)
                           .resize(height=self.height)
                           .set_position('center'))
                
                # REMOVED ZOOM EFFECT to prevent "shaky" look
                
                video_clips.append(img_clip)
                print(f"Scene {i+1}: {word_count} words -> {duration:.2f}s")
            
            # Combine all clips
            if not video_clips:
                raise Exception("No valid video clips created")
            
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Add audio
            final_video = final_video.set_audio(audio_clip)
            
            # Ensure video matches audio duration
            final_video = final_video.set_duration(total_duration)
            
            # Add subtle fade in/out
            final_video = final_video.fadeout(0.5).fadein(0.5)
            
            # Output filename
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_path = f"{self.output_dir}/{safe_title.replace(' ', '_')}_philosophy_video.mp4"
            
            # Render video optimized for TikTok
            print("Rendering video...")
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='medium',  # Good balance of speed and quality
                ffmpeg_params=['-crf', '23']  # Good quality compression
            )
            
            print(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating video: {e}")
            return None
    
    def add_text_overlays(self, video_clip: VideoClip, scenes: List[Dict]) -> VideoClip:
        """Add text overlays for key philosophical concepts"""
        
        text_clips = []
        current_time = 0
        
        for scene in scenes:
            duration = float(scene.get('duration', 7))
            key_concept = scene.get('key_concept', '')
            
            if key_concept:
                # Create text clip
                txt_clip = (TextClip(key_concept.upper(), 
                                   fontsize=40, 
                                   color='#FFD700',  # Gold color
                                   font='Arial-Bold',
                                   stroke_color='black',
                                   stroke_width=2)
                           .set_position(('center', 0.85))  # Bottom of screen
                           .set_duration(3)  # Show for 3 seconds
                           .set_start(current_time + duration - 3)  # Show at end of scene
                           .fadeout(0.5))
                
                text_clips.append(txt_clip)
            
            current_time += duration
        
        if text_clips:
            video_clip = CompositeVideoClip([video_clip] + text_clips)
        
        return video_clip
    
    def create_intro_outro(self, duration: float = 2.0) -> VideoClip:
        """Create intro/outro clip for philosophy app promotion"""
        
        # Create a simple dark background with golden text
        intro_clip = (ColorClip(size=(self.width, self.height), 
                               color=(26, 26, 26), 
                               duration=duration)
                     .set_fps(self.fps))
        
        # Add app promotion text
        title_text = (TextClip("Explore Philosophy", 
                              fontsize=60, 
                              color='#FFD700',
                              font='Arial-Bold')
                     .set_position('center')
                     .set_duration(duration)
                     .fadeout(0.5))
        
        subtitle_text = (TextClip("Download our app to dive deeper", 
                                fontsize=30, 
                                color='white',
                                font='Arial')
                       .set_position(('center', 0.7))
                       .set_duration(duration)
                       .fadeout(0.5))
        
        return CompositeVideoClip([intro_clip, title_text, subtitle_text])
    
    def optimize_for_tiktok(self, video_path: str) -> str:
        """Additional optimizations for TikTok upload"""
        
        try:
            # Load the video
            video = VideoFileClip(video_path)
            
            # Ensure perfect TikTok dimensions and settings
            optimized_video = (video
                             .resize(height=1920)
                             .crop(width=1080, height=1920, x_center=video.w/2, y_center=video.h/2))
            
            # Output optimized version
            optimized_path = video_path.replace('.mp4', '_tiktok_optimized.mp4')
            
            optimized_video.write_videofile(
                optimized_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                bitrate="1000k",  # TikTok recommended
                preset='fast'
            )
            
            video.close()
            optimized_video.close()
            
            return optimized_path
            
        except Exception as e:
            print(f"Error optimizing for TikTok: {e}")
            return video_path

# Example usage
if __name__ == "__main__":
    # Test video assembly with dummy data
    test_scenes = [
        {"scene_number": 1, "duration": 8, "text": "Test scene 1", "key_concept": "Reality"},
        {"scene_number": 2, "duration": 8, "text": "Test scene 2", "key_concept": "Illusion"},
    ]
    
    assembler = VideoAssembler()
    print("Video assembler initialized successfully")