"""
fal.ai Image-to-Video Generator

Uses the MiniMax Hailuo-02 model to create smooth transition videos 
between consecutive scene images for documentary-style content.
"""

import os
import fal_client
import requests
from typing import List, Optional, Callable
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from dotenv import load_dotenv

# Fix for Pillow 10+ compatibility
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

load_dotenv()


class FalVideoGenerator:
    """Generate transition videos between images using fal.ai's MiniMax Hailuo-02 model"""
    
    # Documentary-style transition prompt template
    TRANSITION_PROMPT_TEMPLATE = """Artistic cinematic transition in a dark, candlelit ancient chamber, \
historical documentary style with high contrast and warm golden tones. \
{scene_description}. \
The scene remains still as analog TV static interference slowly builds, \
white noise pixels flickering and scrambling in black-and-white static bursts, \
like an old television losing signal, with scan lines and horizontal hold \
glitches intensifying. The camera slowly and smoothly dollies in. \
Photorealistic oil painting texture, epic historical atmosphere, \
deliberate and precise visual effects only."""

    def __init__(self, api_key: str = None, resolution: str = "768P"):
        """
        Initialize the fal.ai video generator.
        
        Args:
            api_key: fal.ai API key (defaults to FAL_KEY env var)
            resolution: Video resolution - "768P" or "1080P" (default: 768P)
        """
        self.api_key = api_key or os.getenv('FAL_KEY')
        if not self.api_key:
            raise ValueError("FAL_KEY not found. Please set FAL_KEY in .env file")
        
        # Set the API key for fal_client
        os.environ['FAL_KEY'] = self.api_key
        
        self.resolution = resolution
        self.output_dir = "generated_videos"
        self.clips_dir = os.path.join(self.output_dir, "clips")
        os.makedirs(self.clips_dir, exist_ok=True)
        
        # Model endpoint - MiniMax Hailuo-02 standard (supports start + end image)
        self.model_id = "fal-ai/minimax/hailuo-02/standard/image-to-video"
    
    def upload_image(self, local_path: str) -> str:
        """
        Upload a local image to fal.ai storage.
        
        Args:
            local_path: Path to local image file
            
        Returns:
            fal.ai URL of uploaded image
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Image not found: {local_path}")
        
        print(f"Uploading image: {local_path}")
        url = fal_client.upload_file(local_path)
        print(f"Uploaded to: {url}")
        return url
    
    def generate_transition_video(
        self, 
        start_image_url: str, 
        end_image_url: str,
        prompt: str,
        scene_number: int = 1,
        story_title: str = "transition",
        duration: str = "6"
    ) -> Optional[str]:
        """
        Generate a transition video from start image to end image.
        
        The video will start on the first image frame and smoothly transition
        to end on the second image frame, creating a continuous flow when
        chained together.
        
        Args:
            start_image_url: fal.ai URL of starting image (first frame)
            end_image_url: fal.ai URL of ending image (last frame)
            prompt: Description of the transition/scene
            scene_number: Scene number for filename
            story_title: Story title for filename
            duration: Video duration in seconds ("5" or "6")
            
        Returns:
            Local path to downloaded MP4, or None on failure
        """
        print(f"\n🎬 Generating transition {scene_number}: Image {scene_number} → Image {scene_number + 1}")
        print(f"   Start frame: {start_image_url[:60]}...")
        print(f"   End frame:   {end_image_url[:60]}...")
        
        try:
            # Build arguments matching the API spec exactly
            # image_url = starting frame, end_image_url = ending frame
            arguments = {
                "prompt": prompt,
                "image_url": start_image_url,
                "end_image_url": end_image_url,
                "duration": duration,
                "prompt_optimizer": True,
                "resolution": self.resolution,
            }
            
            print(f"   Calling fal.ai API...")
            
            # Call fal.ai image-to-video API with queue updates
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        print(f"   [fal] {log.get('message', log)}")
            
            result = fal_client.subscribe(
                self.model_id,
                arguments=arguments,
                with_logs=True,
                on_queue_update=on_queue_update,
            )
            
            # Get video URL from result
            video_url = result.get('video', {}).get('url')
            if not video_url:
                print(f"Error: No video URL in response: {result}")
                return None
            
            print(f"   ✅ Video generated!")
            
            # Download the video
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            output_path = os.path.join(self.clips_dir, f"{safe_title}_transition_{scene_number}.mp4")
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"   📥 Downloaded to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating transition video: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_all_transitions(
        self, 
        image_paths: List[str],
        story_title: str,
        scene_descriptions: List[str] = None,
        progress_callback: Callable[[int, int, str], None] = None,
        duration: str = "6",
        scene_durations: List[str] = None
    ) -> List[str]:
        """
        Generate transition videos for all consecutive image pairs.
        
        Creates a continuous video by chaining transitions:
        - Transition 1: Image 1 (start) → Image 2 (end)
        - Transition 2: Image 2 (start) → Image 3 (end)  
        - Transition 3: Image 3 (start) → Image 4 (end)
        - ...and so on
        
        Each video clip ends on the same frame that the next clip starts on,
        creating seamless continuity when concatenated.
        
        Args:
            image_paths: List of local image paths (in order)
            story_title: Title of the story for filenames
            scene_descriptions: Optional list of descriptions for each transition
            progress_callback: Optional callback(current, total, status_message)
            duration: Default duration per clip in seconds ("5" or "6")
            scene_durations: Optional list of durations for each scene (e.g., ["6", "5", "6", ...])
                            If provided, overrides the default duration for each clip.
            
        Returns:
            List of local MP4 paths for all transition videos
        """
        if len(image_paths) < 2:
            raise ValueError("Need at least 2 images to create transitions")
        
        num_images = len(image_paths)
        num_transitions = num_images - 1
        
        print(f"\n🎥 Creating continuous video from {num_images} images")
        print(f"   This will generate {num_transitions} transition clips:")
        
        # Log durations if per-scene durations provided
        if scene_durations:
            for i in range(num_transitions):
                dur = scene_durations[i] if i < len(scene_durations) else duration
                print(f"   • Clip {i+1}: Image {i+1} → Image {i+2} ({dur}s)")
        else:
            for i in range(num_transitions):
                print(f"   • Clip {i+1}: Image {i+1} → Image {i+2} ({duration}s)")
        
        # Upload all images first
        print("\n📤 Uploading all images to fal.ai...")
        uploaded_urls = []
        for i, path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i + 1, num_images, f"Uploading image {i + 1}/{num_images}")
            url = self.upload_image(path)
            uploaded_urls.append(url)
        
        print(f"   ✅ All {num_images} images uploaded")
        
        # Generate transitions - each one starts where the previous ended
        print("\n🎬 Generating transition clips...")
        video_paths = []
        
        for i in range(num_transitions):
            if progress_callback:
                progress_callback(i + 1, num_transitions, f"Generating clip {i + 1}/{num_transitions}")
            
            # The start image for this clip is image[i]
            # The end image for this clip is image[i+1]
            # This means clip[i] ends on the same frame that clip[i+1] starts on
            start_idx = i
            end_idx = i + 1
            
            # Build prompt for this transition
            if scene_descriptions and i < len(scene_descriptions):
                scene_desc = scene_descriptions[i]
            else:
                scene_desc = f"Scene {i + 1} transitioning to scene {i + 2}"
            
            prompt = self.TRANSITION_PROMPT_TEMPLATE.format(scene_description=scene_desc)
            
            # Get duration for this specific scene (if per-scene durations provided)
            clip_duration = duration
            if scene_durations and i < len(scene_durations):
                clip_duration = str(scene_durations[i])
            
            video_path = self.generate_transition_video(
                start_image_url=uploaded_urls[start_idx],
                end_image_url=uploaded_urls[end_idx],
                prompt=prompt,
                scene_number=i + 1,
                story_title=story_title,
                duration=clip_duration
            )
            
            if video_path:
                video_paths.append(video_path)
            else:
                print(f"⚠️ Warning: Failed to generate transition {i + 1}")
        
        print(f"\n✅ Generated {len(video_paths)}/{num_transitions} transition clips")
        
        if len(video_paths) == num_transitions:
            print("   All clips created successfully - ready for concatenation!")
        
        return video_paths
    
    def concatenate_videos(
        self, 
        video_paths: List[str], 
        story_title: str,
        crossfade_duration: float = 0.5
    ) -> Optional[str]:
        """
        Concatenate all transition videos into a single video.
        
        Args:
            video_paths: List of video file paths
            story_title: Title for output filename
            crossfade_duration: Duration of crossfade between clips (seconds)
            
        Returns:
            Path to concatenated video, or None on failure
        """
        if not video_paths:
            print("No videos to concatenate")
            return None
        
        print(f"\n🎬 Concatenating {len(video_paths)} video clips...")
        
        try:
            clips = []
            for path in video_paths:
                if os.path.exists(path):
                    clip = VideoFileClip(path)
                    clips.append(clip)
                else:
                    print(f"Warning: Video not found: {path}")
            
            if not clips:
                print("No valid video clips found")
                return None
            
            # Apply crossfades
            if len(clips) > 1 and crossfade_duration > 0:
                processed_clips = []
                current_start = 0
                
                for i, clip in enumerate(clips):
                    clip = clip.set_start(current_start)
                    
                    if i > 0:
                        clip = clip.crossfadein(crossfade_duration)
                    if i < len(clips) - 1:
                        clip = clip.crossfadeout(crossfade_duration)
                    
                    processed_clips.append(clip)
                    current_start += clip.duration - crossfade_duration
                
                # Calculate final size from first clip
                size = (clips[0].w, clips[0].h)
                final_video = CompositeVideoClip(processed_clips, size=size)
            else:
                final_video = concatenate_videoclips(clips, method="compose")
            
            # Output path
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            output_path = os.path.join(self.output_dir, f"{safe_title}_transitions.mp4")
            
            # Write video
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=['-crf', '23']
            )
            
            # Cleanup
            for clip in clips:
                clip.close()
            final_video.close()
            
            print(f"✅ Concatenated video saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error concatenating videos: {e}")
            return None
    
    def create_final_video_with_audio(
        self,
        video_paths: List[str],
        audio_path: str,
        story_title: str,
        crossfade_duration: float = 0.5
    ) -> Optional[str]:
        """
        Create final video with concatenated clips and voiceover audio.
        
        Args:
            video_paths: List of transition video paths
            audio_path: Path to voiceover audio file
            story_title: Title for output filename
            crossfade_duration: Duration of crossfade between clips
            
        Returns:
            Path to final video with audio, or None on failure
        """
        print(f"\n🎬 Creating final video with audio...")
        
        try:
            # First concatenate videos
            concatenated_path = self.concatenate_videos(
                video_paths, 
                f"{story_title}_temp",
                crossfade_duration
            )
            
            if not concatenated_path:
                return None
            
            # Load video and audio
            video = VideoFileClip(concatenated_path)
            audio = AudioFileClip(audio_path)
            
            video_duration = video.duration
            audio_duration = audio.duration
            
            print(f"   Video duration: {video_duration:.2f}s")
            print(f"   Audio duration: {audio_duration:.2f}s")
            
            # Sync strategy: adjust video speed to match audio
            # This is the safest approach - slight slow-down is less noticeable than freeze frames
            if abs(audio_duration - video_duration) > 0.5:  # Only adjust if difference > 0.5s
                speed_factor = video_duration / audio_duration
                
                if speed_factor > 1:
                    # Video is longer than audio - speed up video
                    adjustment = (speed_factor - 1) * 100
                    print(f"   Speeding up video by {adjustment:.1f}%")
                    video = video.speedx(speed_factor)
                else:
                    # Audio is longer than video - slow down video
                    # This stretches the video to match audio length
                    adjustment = (1 - speed_factor) * 100
                    print(f"   Slowing down video by {adjustment:.1f}%")
                    video = video.speedx(speed_factor)
                
                # Log the adjustment quality
                if abs(1 - speed_factor) <= 0.15:
                    print(f"   ✅ Adjustment is within 15% - should look natural")
                elif abs(1 - speed_factor) <= 0.25:
                    print(f"   ⚠️ Adjustment is {abs(1-speed_factor)*100:.0f}% - may be slightly noticeable")
                else:
                    print(f"   ❌ Large adjustment ({abs(1-speed_factor)*100:.0f}%) - consider regenerating with better timing")
            else:
                print(f"   ✅ Duration difference is minimal ({abs(audio_duration - video_duration):.2f}s)")
            
            # Set audio
            final = video.set_audio(audio)
            
            # Ensure duration matches audio
            final = final.set_duration(audio_duration)
            
            # Add fade in/out
            final = final.fadein(0.5).fadeout(0.5)
            
            # Output path
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            output_path = os.path.join(self.output_dir, f"{safe_title}_final_with_audio.mp4")
            
            # Write final video
            final.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=['-crf', '23']
            )
            
            # Cleanup
            video.close()
            audio.close()
            final.close()
            
            # Remove temp concatenated file
            if os.path.exists(concatenated_path):
                os.remove(concatenated_path)
            
            print(f"✅ Final video with audio saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating final video with audio: {e}")
            return None


def check_fal_available() -> bool:
    """Check if fal.ai is configured and available"""
    api_key = os.getenv('FAL_KEY')
    return bool(api_key)


# Example usage
if __name__ == "__main__":
    if not check_fal_available():
        print("FAL_KEY not found in environment. Please set it in .env")
    else:
        print("fal.ai configured and ready!")
        
        # Test with sample images
        gen = FalVideoGenerator()
        
        # List available images
        import glob
        images = sorted(glob.glob("generated_images/*_scene_*_nano.png"))
        print(f"Found {len(images)} images")
        
        if len(images) >= 2:
            print("\nTo test, run:")
            print("  gen.generate_all_transitions(images[:3], 'test_story')")
