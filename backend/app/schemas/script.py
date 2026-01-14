"""Pydantic schemas for Script generation API."""
from typing import Optional
from pydantic import BaseModel, Field


class ScriptGenerateRequest(BaseModel):
    """Request schema for generating a script."""
    topic: str = Field(..., min_length=3, description="Topic for the script")
    content_type: Optional[str] = Field(
        default=None,
        pattern="^(list_educational|list_existential|wisdom_slideshow|narrative_story|list|narrative|mentor_slideshow|auto)$",
        description="Content type: list_educational, list_existential, wisdom_slideshow, narrative_story (or legacy: list, narrative, mentor_slideshow)"
    )
    image_style: Optional[str] = Field(
        default=None,
        pattern="^(classical|surreal|cinematic|minimal)$",
        description="Image style: classical, surreal, cinematic, minimal"
    )
    num_slides: Optional[int] = Field(
        default=None,
        ge=3,
        le=15,
        description="Number of slides to generate"
    )


class ScriptSlide(BaseModel):
    """A single slide in a generated script."""
    title: str
    subtitle: Optional[str] = None
    visual_description: str
    narration: Optional[str] = None


class ScriptGenerateResponse(BaseModel):
    """Response schema for generated script."""
    project_id: str
    topic: str
    content_type: str  # 'list' or 'narrative'
    slides: list[ScriptSlide]
    total_slides: int


class ScriptRegenerateRequest(BaseModel):
    """Request to regenerate a specific slide's script."""
    slide_id: str
    instruction: Optional[str] = Field(
        default=None,
        description="Optional instruction for regeneration"
    )
