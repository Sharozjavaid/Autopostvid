"""API routes for gallery operations."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from ..database import get_db
from ..models.gallery_item import GalleryItem

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


# ============================================================================
# Schemas
# ============================================================================

class GalleryItemCreate(BaseModel):
    """Schema for creating a gallery item."""
    item_type: str = "slide"
    project_id: Optional[str] = None
    slide_id: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    text_content: Optional[str] = None
    font: Optional[str] = None
    theme: Optional[str] = None
    content_style: Optional[str] = None
    metadata: Optional[dict] = None  # Maps to extra_data in model
    status: str = "complete"
    session_id: Optional[str] = None


class GalleryItemUpdate(BaseModel):
    """Schema for updating a gallery item."""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class GalleryItemResponse(BaseModel):
    """Response schema for gallery item."""
    id: str
    item_type: str
    project_id: Optional[str]
    slide_id: Optional[str]
    title: Optional[str]
    subtitle: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    thumbnail_url: Optional[str]
    text_content: Optional[str]
    font: Optional[str]
    theme: Optional[str]
    content_style: Optional[str]
    metadata: Optional[dict]
    status: str
    session_id: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class GalleryListResponse(BaseModel):
    """Response schema for gallery list."""
    items: List[GalleryItemResponse]
    total: int
    has_more: bool


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=GalleryListResponse)
async def list_gallery_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all gallery items with optional filtering."""
    query = db.query(GalleryItem)
    
    if item_type:
        query = query.filter(GalleryItem.item_type == item_type)
    if status:
        query = query.filter(GalleryItem.status == status)
    if project_id:
        query = query.filter(GalleryItem.project_id == project_id)
    
    total = query.count()
    items = query.order_by(desc(GalleryItem.created_at)).offset(offset).limit(limit).all()
    
    return GalleryListResponse(
        items=[GalleryItemResponse(**item.to_dict()) for item in items],
        total=total,
        has_more=offset + len(items) < total,
    )


@router.post("", response_model=GalleryItemResponse)
async def create_gallery_item(
    item: GalleryItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new gallery item."""
    gallery_item = GalleryItem(
        item_type=item.item_type,
        project_id=item.project_id,
        slide_id=item.slide_id,
        title=item.title,
        subtitle=item.subtitle,
        description=item.description,
        image_url=item.image_url,
        thumbnail_url=item.thumbnail_url,
        text_content=item.text_content,
        font=item.font,
        theme=item.theme,
        content_style=item.content_style,
        extra_data=item.metadata,  # Map metadata from API to extra_data in model
        status=item.status,
        session_id=item.session_id,
    )
    
    db.add(gallery_item)
    db.commit()
    db.refresh(gallery_item)
    
    return GalleryItemResponse(**gallery_item.to_dict())


@router.get("/{item_id}", response_model=GalleryItemResponse)
async def get_gallery_item(
    item_id: str,
    db: Session = Depends(get_db),
):
    """Get a single gallery item by ID."""
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    return GalleryItemResponse(**item.to_dict())


@router.put("/{item_id}", response_model=GalleryItemResponse)
async def update_gallery_item(
    item_id: str,
    update: GalleryItemUpdate,
    db: Session = Depends(get_db),
):
    """Update a gallery item."""
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    return GalleryItemResponse(**item.to_dict())


@router.delete("/{item_id}")
async def delete_gallery_item(
    item_id: str,
    db: Session = Depends(get_db),
):
    """Delete a gallery item."""
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    db.delete(item)
    db.commit()
    
    return {"success": True, "message": "Gallery item deleted"}


@router.delete("")
async def clear_gallery(
    db: Session = Depends(get_db),
):
    """Clear all gallery items."""
    count = db.query(GalleryItem).delete()
    db.commit()
    return {"success": True, "deleted": count}


@router.get("/stats/summary")
async def get_gallery_stats(
    db: Session = Depends(get_db),
):
    """Get gallery statistics."""
    total = db.query(GalleryItem).count()
    
    # Count by type
    types = {}
    for item_type in ["slide", "script", "prompt", "image", "project"]:
        types[item_type] = db.query(GalleryItem).filter(GalleryItem.item_type == item_type).count()
    
    # Count by status
    statuses = {}
    for status in ["complete", "draft", "failed"]:
        statuses[status] = db.query(GalleryItem).filter(GalleryItem.status == status).count()
    
    # Unique projects
    projects = db.query(GalleryItem.project_id).filter(GalleryItem.project_id.isnot(None)).distinct().count()
    
    return {
        "total": total,
        "by_type": types,
        "by_status": statuses,
        "unique_projects": projects,
    }
