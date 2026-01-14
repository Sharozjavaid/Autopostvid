"""Pydantic schemas for Slide API."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SlideCreate(BaseModel):
    """Schema for creating a slide."""
    order_index: int = 0
    title: Optional[str] = None
    subtitle: Optional[str] = None
    visual_description: Optional[str] = None
    narration: Optional[str] = None


class SlideUpdate(BaseModel):
    """Schema for updating a slide."""
    order_index: Optional[int] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    visual_description: Optional[str] = None
    narration: Optional[str] = None


class SlideResponse(BaseModel):
    """Schema for slide API responses."""
    id: str
    project_id: str
    order_index: int
    title: Optional[str] = None
    subtitle: Optional[str] = None
    visual_description: Optional[str] = None
    narration: Optional[str] = None
    background_image_path: Optional[str] = None
    final_image_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    image_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SlideReorder(BaseModel):
    """Schema for reordering slides."""
    slide_ids: list[str] = Field(..., description="Ordered list of slide IDs")


class SlideBatchUpdate(BaseModel):
    """Schema for batch updating slides."""
    slides: list[SlideUpdate]
