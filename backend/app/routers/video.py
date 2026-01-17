"""API routes for image-to-video generation."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/video", tags=["video"])


# ============================================================================
# Schemas
# ============================================================================

class SingleTransitionRequest(BaseModel):
    """Request to generate a single video transition."""
    start_image: str  # Path or URL
    end_image: str    # Path or URL
    prompt: str
    duration: str = "6"  # "5" or "6"
    output_name: Optional[str] = None


class NarrationVideoRequest(BaseModel):
    """Request to generate a full narration video."""
    image_paths: List[str]
    scene_descriptions: Optional[List[str]] = None
    title: str = "narration_video"
    duration_per_scene: str = "6"
    prompt_style: str = "documentary"  # "documentary" or "default"


class TransitionResponse(BaseModel):
    """Response from transition generation."""
    success: bool
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[int] = None


# ============================================================================
# Routes
# ============================================================================

@router.post("/transition", response_model=TransitionResponse)
async def generate_transition(request: SingleTransitionRequest):
    """
    Generate a single video transition between two images.
    
    Uses the MiniMax Hailuo-02 model to create a 5-6 second video
    that smoothly transitions from the start image to the end image.
    
    Cost: ~$0.27 per 6-second clip
    """
    try:
        from ..services.image_to_video import get_image_to_video_service
        
        service = get_image_to_video_service()
        result = service.generate_single_transition(
            start_image=request.start_image,
            end_image=request.end_image,
            prompt=request.prompt,
            duration=request.duration,
            output_name=request.output_name
        )
        
        return TransitionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/narration")
async def generate_narration_video(request: NarrationVideoRequest):
    """
    Generate a full narration video with transitions between all images.
    
    This creates a cinematic video where each scene flows into the next.
    For N images, generates N-1 transition clips.
    
    Cost: ~$0.27 per clip × (N-1) clips
    """
    try:
        from ..services.image_to_video import get_image_to_video_service
        
        service = get_image_to_video_service()
        result = service.generate_narration_video(
            image_paths=request.image_paths,
            scene_descriptions=request.scene_descriptions,
            title=request.title,
            duration_per_scene=request.duration_per_scene,
            prompt_style=request.prompt_style
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_video_info():
    """Get information about the image-to-video service."""
    return {
        "model": "fal-ai/minimax/hailuo-02/standard/image-to-video",
        "capabilities": {
            "start_end_frames": True,
            "prompt_guided": True,
            "durations": ["5", "6"],
            "resolutions": ["768P", "1080P"],
        },
        "cost_per_second": 0.045,
        "cost_per_6s_clip": 0.27,
        "prompt_styles": ["documentary", "default"],
        "use_cases": [
            "Transform slideshow into cinematic video",
            "Create smooth transitions between scenes",
            "Bring static images to life",
            "Generate philosophical narration videos"
        ],
        "tips": [
            "Use scene descriptions that describe motion and mood",
            "Documentary style adds TV static glitch effects",
            "6 second clips give more time for smooth transitions",
            "Works best with images that have similar compositions"
        ]
    }
