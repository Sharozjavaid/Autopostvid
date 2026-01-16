"""API routes for inspiration/reference library."""
import os
import sys
import json
import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path so we can import reference_scraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import reference_scraper

router = APIRouter(prefix="/api/inspiration", tags=["inspiration"])


# ============================================================================
# Schemas
# ============================================================================

class ReferenceCreate(BaseModel):
    """Schema for creating a reference from URL."""
    url: str
    format_type: str = "unknown"
    tags: List[str] = []
    notes: str = ""


class ManualReferenceCreate(BaseModel):
    """Schema for creating a manual reference."""
    title: str
    format_type: str = "slideshow"
    tags: List[str] = []
    notes: str = ""
    url: str = ""
    uploader: str = ""
    view_count: int = 0
    like_count: int = 0


class ReferenceUpdate(BaseModel):
    """Schema for updating a reference."""
    title: Optional[str] = None
    format_type: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None


class ReferenceResponse(BaseModel):
    """Response schema for a reference."""
    id: str
    url: str
    format_type: str
    tags: List[str]
    notes: str
    title: str
    uploader: str
    view_count: int
    like_count: int
    frame_count: int
    added_date: str
    is_manual: bool = False


class ReferenceDetailResponse(ReferenceResponse):
    """Detailed response including frames."""
    description: str = ""
    duration: int = 0
    frames: List[str] = []
    video_path: Optional[str] = None


class ReferenceListResponse(BaseModel):
    """Response for listing references."""
    references: List[ReferenceResponse]
    total: int


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=ReferenceListResponse)
async def list_references(
    format_type: Optional[str] = Query(None, description="Filter by format type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
):
    """List all inspiration references."""
    tag_list = tags.split(",") if tags else None
    refs = reference_scraper.list_references(format_type=format_type, tags=tag_list)

    return ReferenceListResponse(
        references=[ReferenceResponse(**r, is_manual=r.get("is_manual", False)) for r in refs],
        total=len(refs),
    )


@router.get("/{ref_id}", response_model=ReferenceDetailResponse)
async def get_reference(ref_id: str):
    """Get a single reference with full details."""
    ref = reference_scraper.get_reference(ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")

    return ReferenceDetailResponse(**ref)


@router.get("/{ref_id}/frame/{frame_index}")
async def get_reference_frame(ref_id: str, frame_index: int):
    """Get a specific frame image from a reference."""
    ref = reference_scraper.get_reference(ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")

    if frame_index < 0 or frame_index >= len(ref.get("frames", [])):
        raise HTTPException(status_code=404, detail="Frame not found")

    frame_path = ref["frames"][frame_index]

    # If path is relative, make it absolute using reference_scraper's base dir
    if not os.path.isabs(frame_path):
        frame_path = str(reference_scraper._SCRIPT_DIR / frame_path)

    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail=f"Frame file not found: {frame_path}")

    return FileResponse(frame_path, media_type="image/jpeg")


@router.get("/{ref_id}/frames")
async def get_all_frame_urls(ref_id: str):
    """Get URLs for all frames of a reference."""
    ref = reference_scraper.get_reference(ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")

    frames = ref.get("frames", [])
    return {
        "ref_id": ref_id,
        "frame_count": len(frames),
        "frame_urls": [f"/api/inspiration/{ref_id}/frame/{i}" for i in range(len(frames))],
    }


@router.post("/scrape", response_model=ReferenceResponse)
async def scrape_tiktok(data: ReferenceCreate, background_tasks: BackgroundTasks):
    """
    Scrape a TikTok video and add it to the inspiration library.
    Note: This runs in background as it may take time.
    """
    # Run synchronously for now (could be made async with background task)
    ref = reference_scraper.add_reference(
        url=data.url,
        format_type=data.format_type,
        tags=data.tags,
        notes=data.notes,
    )

    if not ref:
        raise HTTPException(status_code=400, detail="Failed to scrape TikTok. The URL may not be supported.")

    return ReferenceResponse(**ref, is_manual=False)


@router.post("/manual", response_model=ReferenceResponse)
async def create_manual_reference(data: ManualReferenceCreate):
    """Create a manual reference entry (for screenshots you'll upload)."""
    ref = reference_scraper.add_manual_reference(
        title=data.title,
        format_type=data.format_type,
        tags=data.tags,
        notes=data.notes,
        url=data.url,
        uploader=data.uploader,
        view_count=data.view_count,
        like_count=data.like_count,
    )

    return ReferenceResponse(**ref, is_manual=True)


@router.post("/{ref_id}/frames")
async def upload_frame(
    ref_id: str,
    file: UploadFile = File(...),
    frame_name: Optional[str] = Form(None),
):
    """Upload a frame/screenshot to an existing reference."""
    ref = reference_scraper.get_reference(ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")

    # Read file content
    content = await file.read()

    # Add frame
    updated_ref = reference_scraper.add_frame_to_reference(
        ref_id=ref_id,
        frame_data=content,
        frame_name=frame_name,
    )

    if not updated_ref:
        raise HTTPException(status_code=500, detail="Failed to add frame")

    return {
        "success": True,
        "ref_id": ref_id,
        "frame_count": updated_ref["frame_count"],
        "latest_frame": updated_ref["frames"][-1] if updated_ref["frames"] else None,
    }


@router.put("/{ref_id}", response_model=ReferenceResponse)
async def update_reference(ref_id: str, data: ReferenceUpdate):
    """Update reference metadata."""
    updates = data.model_dump(exclude_unset=True)

    ref = reference_scraper.update_reference_metadata(ref_id, updates)
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")

    return ReferenceResponse(**ref, is_manual=ref.get("is_manual", False))


@router.delete("/{ref_id}")
async def delete_reference(ref_id: str):
    """Delete a reference and all its files."""
    success = reference_scraper.delete_reference(ref_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reference not found")

    return {"success": True, "message": f"Reference {ref_id} deleted"}


@router.get("/formats/list")
async def list_format_types():
    """Get list of available format types."""
    return {
        "format_types": [
            {"id": "slideshow", "name": "Slideshow", "description": "Static image carousel"},
            {"id": "narrated_video", "name": "Narrated Video", "description": "Video with voiceover"},
            {"id": "mentor_slideshow", "name": "Mentor Slideshow", "description": "Wisdom/advice format"},
            {"id": "quote_video", "name": "Quote Video", "description": "Single quote with imagery"},
            {"id": "story_video", "name": "Story Video", "description": "Narrative storytelling"},
            {"id": "unknown", "name": "Other", "description": "Uncategorized format"},
        ]
    }


@router.get("/stats/summary")
async def get_inspiration_stats():
    """Get statistics about the inspiration library."""
    refs = reference_scraper.list_references()

    # Count by format type
    by_format = {}
    total_frames = 0
    total_views = 0

    for ref in refs:
        fmt = ref.get("format_type", "unknown")
        by_format[fmt] = by_format.get(fmt, 0) + 1
        total_frames += ref.get("frame_count", 0)
        total_views += ref.get("view_count", 0)

    return {
        "total_references": len(refs),
        "total_frames": total_frames,
        "total_views": total_views,
        "by_format": by_format,
    }
