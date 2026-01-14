from moviepy.editor import *
import os
from typing import List, Dict
import json
import numpy as np

# Fix for Pillow 10+ compatibility (ANTIALIAS was removed)
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS


# ============= TRANSITION EFFECTS =============

def crossfade_transition(clip1, clip2, duration=0.5):
    """Create a crossfade between two clips"""
    # Fade out clip1 and fade in clip2
    clip1_faded = clip1.crossfadeout(duration)
    clip2_faded = clip2.crossfadein(duration)
    
    # Overlap clips
    clip2_faded = clip2_faded.set_start(clip1.duration - duration)
    
    return CompositeVideoClip([clip1_faded, clip2_faded])


def slide_transition(clip1, clip2, duration=0.5, direction="left"):
    """Slide transition - new clip slides in from a direction"""
    
    def slide_in(t, direction, clip_w, duration):
        if direction == "left":
            return max(0, clip_w * (1 - t / duration)), 0
        elif direction == "right":
            return min(0, -clip_w * (1 - t / duration)), 0
        elif direction == "up":
            return 0, max(0, 1920 * (1 - t / duration))
        else:  # down
            return 0, min(0, -1920 * (1 - t / duration))
    
    # Position clip2 to slide in
    clip2_sliding = clip2.set_position(lambda t: slide_in(t, direction, 1080, duration))
    clip2_sliding = clip2_sliding.set_start(clip1.duration - duration)
    
    return CompositeVideoClip([clip1, clip2_sliding], size=(1080, 1920))


def fade_through_black(clip1, clip2, duration=0.3):
    """Fade to black then fade in the next clip"""
    clip1_faded = clip1.fadeout(duration)
    clip2_faded = clip2.fadein(duration).set_start(clip1.duration - duration/2)
    
    return CompositeVideoClip([clip1_faded, clip2_faded])


def zoom_transition(clip1, clip2, duration=0.5, zoom_type="in"):
    """Zoom transition effect"""
    
    def zoom_effect(get_frame, t, duration, zoom_type):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        
        if t < duration:
            progress = t / duration
            if zoom_type == "in":
                scale = 1 + 0.3 * progress  # Zoom in from 1x to 1.3x
            else:
                scale = 1.3 - 0.3 * progress  # Zoom out from 1.3x to 1x
        else:
            scale = 1.0
        
        return frame
    
    return crossfade_transition(clip1, clip2, duration)


# Transition registry
TRANSITIONS = {
    "none": None,
    "crossfade": crossfade_transition,
    "fade_black": fade_through_black,
    "slide_left": lambda c1, c2, d: slide_transition(c1, c2, d, "left"),
    "slide_right": lambda c1, c2, d: slide_transition(c1, c2, d, "right"),
    "slide_up": lambda c1, c2, d: slide_transition(c1, c2, d, "up"),
}


class VideoAssembler:
    def __init__(self):
        self.output_dir = "generated_videos"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # TikTok optimal settings
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
        # Default transition settings
        self.transition_type = "crossfade"
        self.transition_duration = 0.3
    
    def create_philosophy_video(self, 
                              scenes: List[Dict], 
                              audio_path: str, 
                              image_paths: List[str],
                              story_title: str,
                              transition: str = "crossfade",
                              transition_duration: float = 0.3) -> str:
        """Assemble final video using Word-Count Alignment with transitions
        
        Args:
            scenes: List of scene dictionaries
            audio_path: Path to audio file
            image_paths: List of image paths
            story_title: Title for output filename
            transition: Transition type ("none", "crossfade", "fade_black", "slide_left", "slide_right", "slide_up")
            transition_duration: Duration of transition in seconds
        """
        
        try:
            # Load the single continuous audio file
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            print(f"Audio duration: {total_duration} seconds")
            print(f"Transition: {transition} ({transition_duration}s)")
            
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
            
            # Account for transition overlap in duration calculation
            num_transitions = len(scenes) - 1 if transition != "none" else 0
            total_transition_time = num_transitions * transition_duration
            effective_duration = total_duration + total_transition_time  # We'll overlap so add it back
            
            # Create video clips with proportional duration
            video_clips = []
            
            for i, (scene, image_path, word_count) in enumerate(zip(scenes, image_paths, scene_word_counts)):
                if not os.path.exists(image_path):
                    print(f"Warning: Image not found: {image_path}")
                    continue
                
                # proportional duration (add transition time to each clip for overlap)
                proportion = word_count / total_words
                duration = total_duration * proportion
                
                # Add transition buffer to all clips except the last
                if transition != "none" and i < len(scenes) - 1:
                    duration += transition_duration
                
                # Create image clip
                img_clip = (ImageClip(image_path)
                           .set_duration(duration)
                           .resize(height=self.height)
                           .set_position('center'))
                
                video_clips.append(img_clip)
                print(f"Scene {i+1}: {word_count} words -> {duration:.2f}s")
            
            # Combine all clips
            if not video_clips:
                raise Exception("No valid video clips created")
            
            # Apply transitions between clips
            if transition != "none" and transition in TRANSITIONS and len(video_clips) > 1:
                transition_func = TRANSITIONS[transition]
                print(f"Applying {transition} transitions...")
                
                # Build video with transitions using crossfade for reliability
                # Use CompositeVideoClip with proper timing
                composite_clips = []
                current_start = 0
                
                for i, clip in enumerate(video_clips):
                    # Set start time for this clip
                    clip = clip.set_start(current_start)
                    
                    # Apply fade effects for crossfade
                    if transition == "crossfade" or transition == "fade_black":
                        if i > 0:  # Fade in (not first clip)
                            clip = clip.crossfadein(transition_duration)
                        if i < len(video_clips) - 1:  # Fade out (not last clip)
                            clip = clip.crossfadeout(transition_duration)
                    
                    composite_clips.append(clip)
                    
                    # Next clip starts before this one ends (overlap)
                    current_start += clip.duration - transition_duration
                
                final_video = CompositeVideoClip(composite_clips, size=(self.width, self.height))
            else:
                # No transitions - simple concatenation
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