"""Slides API router - CRUD operations for slides."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Slide
from ..schemas import SlideCreate, SlideUpdate, SlideResponse, SlideReorder

router = APIRouter()


def slide_to_response(slide: Slide) -> SlideResponse:
    """Convert Slide model to response schema."""
    return SlideResponse(
        id=slide.id,
        project_id=slide.project_id,
        order_index=slide.order_index,
        title=slide.title,
        subtitle=slide.subtitle,
        visual_description=slide.visual_description,
        narration=slide.narration,
        background_image_path=slide.background_image_path,
        final_image_path=slide.final_image_path,
        video_clip_path=slide.video_clip_path,
        image_status=slide.image_status,
        error_message=slide.error_message,
        created_at=slide.created_at,
        updated_at=slide.updated_at
    )


@router.get("/project/{project_id}", response_model=List[SlideResponse])
async def get_project_slides(project_id: str, db: Session = Depends(get_db)):
    """Get all slides for a project, ordered by index."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    slides = db.query(Slide).filter(
        Slide.project_id == project_id
    ).order_by(Slide.order_index).all()

    return [slide_to_response(s) for s in slides]


@router.post("/project/{project_id}", response_model=SlideResponse, status_code=201)
async def create_slide(
    project_id: str,
    slide_data: SlideCreate,
    db: Session = Depends(get_db)
):
    """Create a new slide for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get max order index
    max_index = db.query(Slide).filter(
        Slide.project_id == project_id
    ).count()

    slide = Slide(
        project_id=project_id,
        order_index=slide_data.order_index if slide_data.order_index is not None else max_index,
        title=slide_data.title,
        subtitle=slide_data.subtitle,
        visual_description=slide_data.visual_description,
        narration=slide_data.narration
    )
    db.add(slide)
    db.commit()
    db.refresh(slide)

    return slide_to_response(slide)


@router.get("/{slide_id}", response_model=SlideResponse)
async def get_slide(slide_id: str, db: Session = Depends(get_db)):
    """Get a slide by ID."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    return slide_to_response(slide)


@router.put("/{slide_id}", response_model=SlideResponse)
async def update_slide(
    slide_id: str,
    slide_data: SlideUpdate,
    db: Session = Depends(get_db)
):
    """Update a slide."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    if slide_data.order_index is not None:
        slide.order_index = slide_data.order_index
    if slide_data.title is not None:
        slide.title = slide_data.title
    if slide_data.subtitle is not None:
        slide.subtitle = slide_data.subtitle
    if slide_data.visual_description is not None:
        slide.visual_description = slide_data.visual_description
        slide.image_status = "pending"  # Reset status when visual changes
    if slide_data.narration is not None:
        slide.narration = slide_data.narration

    db.commit()
    db.refresh(slide)
    return slide_to_response(slide)


@router.delete("/{slide_id}", status_code=204)
async def delete_slide(slide_id: str, db: Session = Depends(get_db)):
    """Delete a slide."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    project_id = slide.project_id
    deleted_index = slide.order_index

    db.delete(slide)

    # Reorder remaining slides
    remaining = db.query(Slide).filter(
        Slide.project_id == project_id,
        Slide.order_index > deleted_index
    ).all()

    for s in remaining:
        s.order_index -= 1

    db.commit()
    return None


@router.post("/project/{project_id}/reorder")
async def reorder_slides(
    project_id: str,
    reorder: SlideReorder,
    db: Session = Depends(get_db)
):
    """Reorder slides in a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update order based on provided list
    for i, slide_id in enumerate(reorder.slide_ids):
        slide = db.query(Slide).filter(
            Slide.id == slide_id,
            Slide.project_id == project_id
        ).first()
        if slide:
            slide.order_index = i

    db.commit()

    return {"success": True, "message": "Slides reordered"}


@router.post("/{slide_id}/duplicate", response_model=SlideResponse)
async def duplicate_slide(slide_id: str, db: Session = Depends(get_db)):
    """Duplicate a slide."""
    original = db.query(Slide).filter(Slide.id == slide_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Slide not found")

    # Shift subsequent slides
    subsequent = db.query(Slide).filter(
        Slide.project_id == original.project_id,
        Slide.order_index > original.order_index
    ).all()

    for s in subsequent:
        s.order_index += 1

    # Create duplicate
    new_slide = Slide(
        project_id=original.project_id,
        order_index=original.order_index + 1,
        title=original.title,
        subtitle=original.subtitle,
        visual_description=original.visual_description,
        narration=original.narration,
        image_status="pending"
    )
    db.add(new_slide)
    db.commit()
    db.refresh(new_slide)

    return slide_to_response(new_slide)
