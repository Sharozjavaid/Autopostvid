"""Pydantic schemas for Image generation API."""
from typing import Optional
from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    """Request schema for generating an image.
    
    Always generates background + programmatic text overlay (Pillow).
    AI-burned text has been removed for consistency.
    """
    model: str = Field(
        default="gpt15",
        pattern="^(gpt15|flux|dalle3)$",
        description="Image generation model for backgrounds"
    )
    font: Optional[str] = Field(
        default="social",
        description="Font for text overlay: social (default), bebas, montserrat, cinzel, oswald, cormorant"
    )
    theme: Optional[str] = Field(
        default="golden_dust",
        description="Visual theme: glitch_titans, oil_contrast, golden_dust, scene_portrait"
    )


class ImageBatchGenerateRequest(BaseModel):
    """Request schema for batch generating images.
    
    Generates backgrounds + applies programmatic text overlay.
    """
    model: str = Field(
        default="gpt15",
        pattern="^(gpt15|flux|dalle3)$",
        description="Image generation model for backgrounds"
    )
    font: Optional[str] = Field(
        default="social",
        description="Font for text overlay: social (default), bebas, montserrat, cinzel, oswald, cormorant"
    )
    theme: Optional[str] = Field(
        default="golden_dust",
        description="Visual theme: glitch_titans, oil_contrast, golden_dust, scene_portrait"
    )
    slide_ids: Optional[list[str]] = Field(
        default=None,
        description="Specific slides to generate (None = all pending)"
    )
    include_cta: bool = Field(
        default=True,
        description="Add CTA slide for Philosophize Me app at the end"
    )


class ImageGenerateResponse(BaseModel):
    """Response schema for image generation."""
    slide_id: str
    status: str  # 'success', 'error', 'pending'
    background_image_url: Optional[str] = None
    final_image_url: Optional[str] = None
    error_message: Optional[str] = None


class ImageBatchGenerateResponse(BaseModel):
    """Response schema for batch image generation."""
    project_id: str
    total_slides: int
    generated: int
    failed: int
    results: list[ImageGenerateResponse]


class ImageProgress(BaseModel):
    """WebSocket message for image generation progress."""
    type: str = "image_progress"
    project_id: str
    slide_id: str
    slide_index: int
    total_slides: int
    status: str
    message: str
    image_url: Optional[str] = None
