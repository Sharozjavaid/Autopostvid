"""
Image-to-Video Service using fal.ai MiniMax Hailuo-02 model.

This service creates cinematic video transitions between images, bringing
static slides to life with AI-generated motion. The model supports:

- Start frame + End frame: Creates a smooth 5-6 second transition between two images
- Prompt-guided motion: Describe how the scene should move/transform
- Documentary-style effects: Camera movements, lighting changes, atmospheric effects

USE CASES:
1. Slideshow → Cinematic Video: Transform static slides into flowing videos
2. Scene Transitions: Create seamless transitions between narrative scenes
3. Image Animation: Bring a single image to life with subtle motion

MODEL DETAILS:
- Model: fal-ai/minimax/hailuo-02/standard/image-to-video
- Duration: 5-6 seconds per clip
- Resolution: 768P or 1080P
- Cost: ~$0.045 per second (~$0.27 per 6-second clip)
"""

import os
import fal_client
import requests
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Import cloud storage for uploading results
try:
    from .cloud_storage import get_storage_service, upload_video_to_gcs
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class ImageToVideoService:
    """
    Generate cinematic video transitions between images.
    
    The MiniMax Hailuo-02 model creates smooth, AI-generated motion between
    a starting frame and ending frame, guided by a text prompt.
    """
    
    # Model endpoint
    MODEL_ID = "fal-ai/minimax/hailuo-02/standard/image-to-video"
    
    # Default transition prompt for philosophical/documentary content
    DEFAULT_PROMPT_TEMPLATE = """Cinematic transition with dramatic lighting and atmospheric depth. 
{description}. 
Slow, deliberate camera movement. Photorealistic style with subtle motion. 
High contrast, warm golden tones mixing with deep shadows."""

    # Epic documentary style prompt
    DOCUMENTARY_PROMPT_TEMPLATE = """Artistic cinematic transition in a dark, candlelit ancient chamber, 
historical documentary style with high contrast and warm golden tones. 
{description}. 
The scene remains still as analog TV static interference slowly builds, 
white noise pixels flickering and scrambling in black-and-white static bursts, 
like an old television losing signal, with scan lines and horizontal hold 
glitches intensifying. The camera slowly and smoothly dollies in. 
Photorealistic oil painting texture, epic historical atmosphere."""

    def __init__(self, api_key: str = None, resolution: str = "768P"):
        """
        Initialize the image-to-video service.
        
        Args:
            api_key: fal.ai API key (defaults to FAL_KEY env var)
            resolution: "768P" (faster/cheaper) or "1080P" (higher quality)
        """
        self.api_key = api_key or os.getenv('FAL_KEY')
        if not self.api_key:
            raise ValueError("FAL_KEY not found in environment")
        
        os.environ['FAL_KEY'] = self.api_key
        self.resolution = resolution
        
        # Output directories
        self.output_dir = Path("generated_videos")
        self.clips_dir = self.output_dir / "clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_image_to_fal(self, local_path: str) -> str:
        """Upload a local image to fal.ai storage and return the URL."""
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Image not found: {local_path}")
        
        url = fal_client.upload_file(local_path)
        return url
    
    def generate_single_transition(
        self,
        start_image: str,
        end_image: str,
        prompt: str,
        duration: str = "6",
        output_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate a single video transition between two images.
        
        Args:
            start_image: Path or URL to starting frame
            end_image: Path or URL to ending frame  
            prompt: Description of the motion/transition
            duration: "5" or "6" seconds
            output_name: Optional name for output file
            
        Returns:
            Dict with success status, video_path, video_url, and metadata
        """
        try:
            # Upload images if they're local paths
            if not start_image.startswith('http'):
                start_url = self.upload_image_to_fal(start_image)
            else:
                start_url = start_image
                
            if not end_image.startswith('http'):
                end_url = self.upload_image_to_fal(end_image)
            else:
                end_url = end_image
            
            # Call fal.ai API
            arguments = {
                "prompt": prompt,
                "image_url": start_url,
                "end_image_url": end_url,
                "duration": duration,
                "prompt_optimizer": True,
                "resolution": self.resolution,
            }
            
            result = fal_client.subscribe(
                self.MODEL_ID,
                arguments=arguments,
                with_logs=True,
            )
            
            # Get video URL
            video_url = result.get('video', {}).get('url')
            if not video_url:
                return {"success": False, "error": "No video URL in response"}
            
            # Download video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_name or f"transition_{timestamp}.mp4"
            output_path = self.clips_dir / filename
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Upload to GCS if available
            gcs_url = None
            if GCS_AVAILABLE:
                gcs_url = upload_video_to_gcs(str(output_path), delete_local=False)
            
            return {
                "success": True,
                "video_path": str(output_path),
                "video_url": gcs_url or f"/static/videos/clips/{filename}",
                "fal_url": video_url,
                "duration_seconds": int(duration),
                "resolution": self.resolution,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_narration_video(
        self,
        image_paths: List[str],
        scene_descriptions: List[str] = None,
        title: str = "narration_video",
        duration_per_scene: str = "6",
        prompt_style: str = "documentary"
    ) -> Dict[str, Any]:
        """
        Generate a full narration video with transitions between all images.
        
        This creates a cinematic video where each scene flows into the next,
        perfect for philosophical narration content.
        
        Args:
            image_paths: List of image paths (in order)
            scene_descriptions: Optional descriptions for each transition
            title: Name for the output video
            duration_per_scene: Duration for each clip ("5" or "6")
            prompt_style: "documentary" (dramatic) or "default" (subtle)
            
        Returns:
            Dict with video clips, total duration, and metadata
        """
        if len(image_paths) < 2:
            return {"success": False, "error": "Need at least 2 images"}
        
        num_transitions = len(image_paths) - 1
        results = []
        
        # Choose prompt template
        template = (self.DOCUMENTARY_PROMPT_TEMPLATE 
                   if prompt_style == "documentary" 
                   else self.DEFAULT_PROMPT_TEMPLATE)
        
        for i in range(num_transitions):
            # Build prompt for this transition
            if scene_descriptions and i < len(scene_descriptions):
                desc = scene_descriptions[i]
            else:
                desc = f"Scene {i+1} flowing into scene {i+2}"
            
            prompt = template.format(description=desc)
            
            # Generate transition
            result = self.generate_single_transition(
                start_image=image_paths[i],
                end_image=image_paths[i + 1],
                prompt=prompt,
                duration=duration_per_scene,
                output_name=f"{title}_clip_{i+1}.mp4"
            )
            
            results.append({
                "clip_number": i + 1,
                "start_image": image_paths[i],
                "end_image": image_paths[i + 1],
                **result
            })
        
        successful = [r for r in results if r.get("success")]
        
        return {
            "success": len(successful) == num_transitions,
            "title": title,
            "total_clips": num_transitions,
            "successful_clips": len(successful),
            "clips": results,
            "total_duration_seconds": len(successful) * int(duration_per_scene),
            "video_paths": [r["video_path"] for r in successful],
        }


def get_image_to_video_service() -> ImageToVideoService:
    """Get an instance of the image-to-video service."""
    return ImageToVideoService()
