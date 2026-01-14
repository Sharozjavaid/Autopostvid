"""Projects API router - CRUD operations for projects."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from ..database import get_db
from ..models import Project, Slide
from ..schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectList
from ..schemas.project import SlideResponse
from ..services.tiktok_poster import TikTokPoster

logger = logging.getLogger(__name__)

router = APIRouter()


def project_to_response(project: Project) -> ProjectResponse:
    """Convert Project model to response schema."""
    slides = sorted(project.slides, key=lambda s: s.order_index)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        topic=project.topic,
        content_type=project.content_type,
        status=project.status,
        settings=project.settings or {},
        created_at=project.created_at,
        updated_at=project.updated_at,
        slides=[SlideResponse(
            id=s.id,
            order_index=s.order_index,
            title=s.title,
            subtitle=s.subtitle,
            visual_description=s.visual_description,
            narration=s.narration,
            background_image_path=s.background_image_path,
            final_image_path=s.final_image_path,
            image_status=s.image_status,
            created_at=s.created_at
        ) for s in slides],
        slide_count=len(slides)
    )


@router.get("", response_model=ProjectList)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all projects with optional filtering."""
    query = db.query(Project)

    if status:
        query = query.filter(Project.status == status)
    if content_type:
        query = query.filter(Project.content_type == content_type)

    total = query.count()
    projects = query.order_by(desc(Project.updated_at)).offset(skip).limit(limit).all()

    return ProjectList(
        projects=[project_to_response(p) for p in projects],
        total=total
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project."""
    project = Project(
        name=project_data.name,
        topic=project_data.topic,
        content_type=project_data.content_type,
        settings=project_data.settings.model_dump() if project_data.settings else {}
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.topic is not None:
        project.topic = project_data.topic
    if project_data.status is not None:
        project.status = project_data.status
    if project_data.settings is not None:
        project.settings = project_data.settings.model_dump()

    db.commit()
    db.refresh(project)
    return project_to_response(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its slides."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, db: Session = Depends(get_db)):
    """Get statistics for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_slides = len(project.slides)
    completed = sum(1 for s in project.slides if s.image_status == "complete")
    pending = sum(1 for s in project.slides if s.image_status == "pending")
    errors = sum(1 for s in project.slides if s.image_status == "error")

    return {
        "project_id": project_id,
        "total_slides": total_slides,
        "completed": completed,
        "pending": pending,
        "errors": errors,
        "progress_percent": (completed / total_slides * 100) if total_slides > 0 else 0
    }


class TikTokPostRequest(BaseModel):
    """Request body for posting to TikTok."""
    caption: Optional[str] = None


@router.post("/{project_id}/post-to-tiktok")
async def post_project_to_tiktok(
    project_id: str,
    request: TikTokPostRequest,
    db: Session = Depends(get_db)
):
    """Post a project's slideshow to TikTok drafts.
    
    This sends all completed slide images to TikTok as a photo slideshow.
    The slideshow will appear in the user's TikTok inbox/drafts.
    """
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all slides sorted by order
    slides = sorted(project.slides, key=lambda s: s.order_index)
    
    # Get completed slides with images
    completed_slides = [s for s in slides if s.image_status == "complete" and s.final_image_path]
    
    if len(completed_slides) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 completed slide images to create a TikTok slideshow"
        )
    
    # Get image paths
    image_paths = [s.final_image_path for s in completed_slides]
    
    # Build caption
    caption = request.caption or project.topic or project.name or "Philosophy Slideshow"
    
    logger.info(f"Posting project {project_id} to TikTok: {len(image_paths)} images, caption='{caption[:50]}...'")
    
    # Post to TikTok
    try:
        poster = TikTokPoster()
        
        if not poster.is_authenticated():
            raise HTTPException(
                status_code=401,
                detail="TikTok not authenticated. Please connect your TikTok account first."
            )
        
        result = poster.post_photo_slideshow(
            image_paths=image_paths,
            caption=caption,
            to_drafts=True,
            photo_cover_index=0
        )
        
        if result.get("success"):
            logger.info(f"Successfully posted to TikTok: publish_id={result.get('publish_id')}")
            return {
                "success": True,
                "publish_id": result.get("publish_id"),
                "image_count": len(image_paths),
                "message": f"Slideshow with {len(image_paths)} images sent to TikTok drafts!"
            }
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"TikTok post failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error posting to TikTok: {e}")
        raise HTTPException(status_code=500, detail=str(e))
