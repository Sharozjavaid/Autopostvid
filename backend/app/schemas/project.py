"""Pydantic schemas for Project API."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    """Project generation settings."""
    image_model: str = "gpt15"  # 'gpt15', 'flux', 'dalle3'
    font: str = "bebas"  # 'bebas', 'montserrat', 'cinzel', etc.
    theme: str = "dark"
    voice_id: Optional[str] = None


class SlideResponse(BaseModel):
    """Slide data for API responses."""
    id: str
    order_index: int
    title: Optional[str] = None
    subtitle: Optional[str] = None
    visual_description: Optional[str] = None
    narration: Optional[str] = None
    background_image_path: Optional[str] = None
    final_image_path: Optional[str] = None
    image_status: str = "pending"
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    topic: Optional[str] = None
    content_type: str = Field(default="slideshow", pattern="^(slideshow|video)$")
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    topic: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|generating|complete|error)$")
    settings: Optional[ProjectSettings] = None


class ProjectResponse(BaseModel):
    """Schema for project API responses."""
    id: str
    name: str
    topic: Optional[str] = None
    content_type: str
    script_style: Optional[str] = None
    status: str
    script_approved: Optional[str] = None
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    slides: list[SlideResponse] = []
    slide_count: int = 0

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """Schema for listing projects."""
    projects: list[ProjectResponse]
    total: int
