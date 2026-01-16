"""API routes for browsing Cloud Storage content."""
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import datetime

from ..services.cloud_storage import get_storage_service

router = APIRouter(prefix="/api/storage", tags=["storage"])


# ============================================================================
# Schemas
# ============================================================================

class StorageItem(BaseModel):
    """A single item in Cloud Storage."""
    name: str
    url: str
    size_bytes: int
    size_human: str
    content_type: str
    folder: str
    created_at: Optional[str] = None
    

class StorageListResponse(BaseModel):
    """Response for listing storage items."""
    items: List[StorageItem]
    total: int
    folder: str


class StorageStatsResponse(BaseModel):
    """Storage statistics."""
    available: bool
    bucket: Optional[str] = None
    total_files: int = 0
    total_size_mb: float = 0
    folders: dict = {}
    public_url: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_content_type(name: str) -> str:
    """Get content type from filename."""
    name_lower = name.lower()
    if name_lower.endswith('.mp4'):
        return 'video/mp4'
    elif name_lower.endswith('.png'):
        return 'image/png'
    elif name_lower.endswith('.jpg') or name_lower.endswith('.jpeg'):
        return 'image/jpeg'
    elif name_lower.endswith('.mp3'):
        return 'audio/mpeg'
    elif name_lower.endswith('.json'):
        return 'application/json'
    return 'application/octet-stream'


# ============================================================================
# Routes
# ============================================================================

@router.get("/browse", response_model=StorageListResponse)
async def browse_storage(
    folder: str = Query("", description="Folder to browse (videos, slides, images, etc.)"),
    file_type: Optional[str] = Query(None, description="Filter by type: video, image, audio"),
    limit: int = Query(100, ge=1, le=500),
):
    """Browse files in Cloud Storage."""
    storage = get_storage_service()
    
    if not storage.is_available:
        return StorageListResponse(items=[], total=0, folder=folder)
    
    try:
        # List blobs with prefix
        prefix = f"{folder}/" if folder else ""
        blobs = list(storage.bucket.list_blobs(prefix=prefix))
        
        items = []
        for blob in blobs:
            # Skip folder markers
            if blob.name.endswith('/') or blob.name.endswith('.keep'):
                continue
            
            # Get folder from path
            parts = blob.name.split('/')
            item_folder = parts[0] if len(parts) > 1 else 'root'
            
            # Get content type
            content_type = blob.content_type or get_content_type(blob.name)
            
            # Filter by type if specified
            if file_type:
                if file_type == 'video' and not content_type.startswith('video/'):
                    continue
                elif file_type == 'image' and not content_type.startswith('image/'):
                    continue
                elif file_type == 'audio' and not content_type.startswith('audio/'):
                    continue
            
            # Build item
            item = StorageItem(
                name=parts[-1] if parts else blob.name,
                url=f"{storage.public_url_base}/{blob.name}",
                size_bytes=blob.size or 0,
                size_human=format_size(blob.size or 0),
                content_type=content_type,
                folder=item_folder,
                created_at=blob.time_created.isoformat() if blob.time_created else None,
            )
            items.append(item)
        
        # Sort by created_at descending (newest first)
        items.sort(key=lambda x: x.created_at or "", reverse=True)
        
        # Apply limit
        items = items[:limit]
        
        return StorageListResponse(
            items=items,
            total=len(items),
            folder=folder or "all",
        )
        
    except Exception as e:
        print(f"Error browsing storage: {e}")
        return StorageListResponse(items=[], total=0, folder=folder)


@router.get("/videos", response_model=StorageListResponse)
async def list_videos(
    limit: int = Query(50, ge=1, le=200),
):
    """List all videos in Cloud Storage."""
    return await browse_storage(folder="videos", file_type="video", limit=limit)


@router.get("/images", response_model=StorageListResponse)
async def list_images(
    limit: int = Query(100, ge=1, le=500),
):
    """List all images in Cloud Storage."""
    return await browse_storage(folder="images", file_type="image", limit=limit)


@router.get("/slides", response_model=StorageListResponse)
async def list_slides(
    limit: int = Query(100, ge=1, le=500),
):
    """List all slides in Cloud Storage."""
    return await browse_storage(folder="slides", file_type="image", limit=limit)


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats():
    """Get Cloud Storage statistics."""
    storage = get_storage_service()
    stats = storage.get_storage_stats()
    return StorageStatsResponse(**stats)


@router.get("/folders")
async def list_folders():
    """List all folders in Cloud Storage."""
    storage = get_storage_service()
    
    if not storage.is_available:
        return {"folders": [], "error": "Storage not available"}
    
    try:
        blobs = list(storage.bucket.list_blobs())
        folders = set()
        
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) > 1:
                folders.add(parts[0])
        
        return {
            "folders": sorted(list(folders)),
            "bucket": storage.bucket_name,
            "public_url": storage.public_url_base,
        }
        
    except Exception as e:
        return {"folders": [], "error": str(e)}
