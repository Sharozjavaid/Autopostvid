"""Automations API router - CRUD for scheduled automations with sample generation."""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import Automation, Project, Slide
from ..services.prompt_config import CONTENT_TYPES, IMAGE_STYLES

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class AutomationCreate(BaseModel):
    """Create automation request with new fields."""
    name: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(default="wisdom_slideshow")
    image_style: str = Field(default="classical")
    topics: List[str] = Field(default_factory=list)
    schedule_times: List[str] = Field(default_factory=list)  # ["09:00", "18:00"]
    schedule_days: List[str] = Field(default_factory=list)  # ["monday", "friday"]
    email_enabled: bool = False
    email_address: Optional[str] = None
    settings: Optional[dict] = None


class AutomationUpdate(BaseModel):
    """Update automation request."""
    name: Optional[str] = None
    content_type: Optional[str] = None
    image_style: Optional[str] = None
    topics: Optional[List[str]] = None
    schedule_times: Optional[List[str]] = None
    schedule_days: Optional[List[str]] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    settings: Optional[dict] = None


class AutomationResponse(BaseModel):
    """Automation response schema."""
    id: str
    name: str
    content_type: Optional[str] = None
    image_style: Optional[str] = None
    topics: Optional[List[str]] = None
    current_topic_index: Optional[int] = 0
    schedule_times: Optional[List[str]] = None
    schedule_days: Optional[List[str]] = None
    email_enabled: Optional[bool] = False
    email_address: Optional[str] = None
    config: Optional[dict] = None  # Legacy field
    status: str
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    successful_runs: Optional[int] = 0
    failed_runs: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def get_gemini_handler():
    """Lazy load GeminiHandler."""
    from ..services.gemini_handler import GeminiHandler
    return GeminiHandler()


@router.get("")
async def list_automations(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all automations."""
    query = db.query(Automation)
    if status:
        query = query.filter(Automation.status == status)

    automations = query.order_by(Automation.created_at.desc()).all()
    return {
        "automations": [a.to_dict() for a in automations],
        "total": len(automations)
    }


@router.post("", status_code=201)
async def create_automation(
    data: AutomationCreate,
    db: Session = Depends(get_db)
):
    """Create a new automation recipe."""
    # Validate content_type
    if data.content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content_type. Must be one of: {list(CONTENT_TYPES.keys())}"
        )

    # Validate image_style
    if data.image_style not in IMAGE_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image_style. Must be one of: {list(IMAGE_STYLES.keys())}"
        )

    automation = Automation(
        name=data.name,
        content_type=data.content_type,
        image_style=data.image_style,
        topics=data.topics,
        schedule_times=data.schedule_times,
        schedule_days=data.schedule_days,
        email_enabled=data.email_enabled,
        email_address=data.email_address,
        settings=data.settings or {
            "auto_approve_script": True,
            "auto_generate_images": True,
            "image_model": "gpt15",
            "font": "social"
        },
        status="stopped",
        is_active=False
    )
    db.add(automation)
    db.commit()
    db.refresh(automation)

    return {
        "success": True,
        "message": "Automation created successfully",
        "automation": automation.to_dict()
    }


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(automation_id: str, db: Session = Depends(get_db)):
    """Get an automation by ID."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    return automation


@router.put("/{automation_id}")
async def update_automation(
    automation_id: str,
    data: AutomationUpdate,
    db: Session = Depends(get_db)
):
    """Update an automation recipe."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    # Update name
    if data.name is not None:
        automation.name = data.name
    
    # Validate and update content_type
    if data.content_type is not None:
        if data.content_type not in CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content_type. Must be one of: {list(CONTENT_TYPES.keys())}"
            )
        automation.content_type = data.content_type
    
    # Validate and update image_style
    if data.image_style is not None:
        if data.image_style not in IMAGE_STYLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image_style. Must be one of: {list(IMAGE_STYLES.keys())}"
            )
        automation.image_style = data.image_style
    
    # Update topics queue
    if data.topics is not None:
        automation.topics = data.topics
    
    # Update schedule
    if data.schedule_times is not None:
        automation.schedule_times = data.schedule_times
    if data.schedule_days is not None:
        automation.schedule_days = data.schedule_days
    
    # Update email settings
    if data.email_enabled is not None:
        automation.email_enabled = data.email_enabled
    if data.email_address is not None:
        automation.email_address = data.email_address
    
    # Update additional settings
    if data.settings is not None:
        automation.settings = data.settings

    db.commit()
    db.refresh(automation)
    
    return {
        "success": True,
        "message": "Automation updated successfully",
        "automation": automation.to_dict()
    }


@router.delete("/{automation_id}", status_code=204)
async def delete_automation(automation_id: str, db: Session = Depends(get_db)):
    """Delete an automation."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    if automation.status == "running":
        raise HTTPException(status_code=400, detail="Cannot delete running automation")

    db.delete(automation)
    db.commit()
    return None


@router.post("/{automation_id}/start")
async def start_automation(automation_id: str, db: Session = Depends(get_db)):
    """Start an automation."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    if automation.status == "running":
        raise HTTPException(status_code=400, detail="Automation already running")

    # TODO: Actually start the background process
    automation.status = "running"
    automation.is_active = True
    db.commit()

    return {"success": True, "message": "Automation started", "status": automation.status}


@router.post("/{automation_id}/stop")
async def stop_automation(automation_id: str, db: Session = Depends(get_db)):
    """Stop an automation."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    # TODO: Actually stop the background process
    automation.status = "stopped"
    automation.is_active = False
    db.commit()

    return {"success": True, "message": "Automation stopped", "status": automation.status}


@router.post("/{automation_id}/pause")
async def pause_automation(automation_id: str, db: Session = Depends(get_db)):
    """Pause an automation."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    if automation.status != "running":
        raise HTTPException(status_code=400, detail="Can only pause running automations")

    automation.status = "paused"
    db.commit()

    return {"success": True, "message": "Automation paused", "status": automation.status}


@router.post("/{automation_id}/resume")
async def resume_automation(automation_id: str, db: Session = Depends(get_db)):
    """Resume a paused automation."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    if automation.status != "paused":
        raise HTTPException(status_code=400, detail="Can only resume paused automations")

    automation.status = "running"
    db.commit()

    return {"success": True, "message": "Automation resumed", "status": automation.status}


@router.post("/{automation_id}/run-once")
async def run_automation_once(
    automation_id: str,
    topic: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Run automation once (for testing).
    
    Generates one slideshow using the automation's config.
    If topic is provided, uses that. Otherwise picks next from topics queue.
    """
    import sys
    from pathlib import Path
    
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    # Get topic from queue if not provided
    if not topic:
        if automation.topics and len(automation.topics) > 0:
            topic = automation.get_next_topic()
        else:
            raise HTTPException(status_code=400, detail="No topics in queue. Add topics first.")
    
    settings = automation.settings or {}
    
    # Import and run pipeline
    try:
        # Add project root to path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from slideshow_pipeline import SlideshowPipeline
        
        pipeline = SlideshowPipeline(
            output_dir="generated_slideshows",
            font=settings.get("font", "social"),
            image_model=settings.get("image_model", "gpt15")
        )
        
        # Get number of slides from content type
        content_config = CONTENT_TYPES.get(automation.content_type, CONTENT_TYPES["wisdom_slideshow"])
        
        result = pipeline.generate_slideshow(
            topic=topic,
            num_slides=content_config.num_slides,
            content_type=automation.content_type,
            image_style=automation.image_style
        )
        
        # Update automation stats
        automation.total_runs += 1
        automation.successful_runs += 1 if result.get("success", False) else 0
        automation.failed_runs += 0 if result.get("success", False) else 1
        automation.last_run = datetime.utcnow()
        automation.advance_topic()  # Move to next topic in queue
        db.commit()
        
        return {
            "success": result.get("success", False),
            "topic": topic,
            "slides": result.get("total_slides", 0),
            "output_dir": result.get("project_dir"),
            "elapsed_seconds": result.get("elapsed_seconds"),
            "total_runs": automation.total_runs
        }
        
    except Exception as e:
        automation.failed_runs += 1
        automation.last_run = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


# =============================================================================
# SAMPLE GENERATION
# =============================================================================

@router.post("/{automation_id}/sample")
async def generate_sample(
    automation_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate a SAMPLE slideshow using this automation's config.
    
    This creates a preview of what the automation will produce:
    - Uses the first topic from the queue (or a default)
    - Generates script using content_type
    - Generates ONE sample image using image_style
    - Does NOT count towards run stats
    - Does NOT advance the topic queue
    """
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    # Get a preview topic
    if automation.topics and len(automation.topics) > 0:
        preview_topic = automation.topics[0]
    else:
        preview_topic = "4 truths about life the ancients understood"
    
    try:
        # Generate script
        gemini = get_gemini_handler()
        script_result = gemini.generate_script(
            topic=preview_topic,
            content_type=automation.content_type
        )
        
        if not script_result:
            raise HTTPException(status_code=500, detail="Failed to generate sample script")
        
        # Get image style config for prompt info
        image_style_config = IMAGE_STYLES.get(automation.image_style, IMAGE_STYLES["classical"])
        
        # Return the sample without actually generating images (expensive)
        return {
            "success": True,
            "preview": True,
            "topic": preview_topic,
            "content_type": automation.content_type,
            "image_style": automation.image_style,
            "script": script_result,
            "image_style_preview": {
                "name": image_style_config.name,
                "description": image_style_config.description,
            },
            "message": "This is a preview of what the automation will generate. Images not rendered to save costs."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample generation failed: {str(e)}")


# =============================================================================
# TOPIC QUEUE MANAGEMENT
# =============================================================================

class TopicAdd(BaseModel):
    """Add topic request."""
    topic: str = Field(..., min_length=1)


class TopicsAdd(BaseModel):
    """Add multiple topics request."""
    topics: List[str]


@router.post("/{automation_id}/topics")
async def add_topic(
    automation_id: str,
    data: TopicAdd,
    db: Session = Depends(get_db)
):
    """Add a single topic to the queue."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    topics = automation.topics or []
    topics.append(data.topic)
    automation.topics = topics
    db.commit()
    
    return {
        "success": True,
        "topics": automation.topics,
        "total": len(automation.topics)
    }


@router.post("/{automation_id}/topics/bulk")
async def add_topics_bulk(
    automation_id: str,
    data: TopicsAdd,
    db: Session = Depends(get_db)
):
    """Add multiple topics to the queue."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    topics = automation.topics or []
    topics.extend([t.strip() for t in data.topics if t.strip()])
    automation.topics = topics
    db.commit()
    
    return {
        "success": True,
        "topics": automation.topics,
        "total": len(automation.topics),
        "added": len(data.topics)
    }


@router.delete("/{automation_id}/topics/{topic_index}")
async def remove_topic(
    automation_id: str,
    topic_index: int,
    db: Session = Depends(get_db)
):
    """Remove a topic from the queue by index."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    topics = automation.topics or []
    if topic_index < 0 or topic_index >= len(topics):
        raise HTTPException(status_code=400, detail="Topic index out of range")
    
    removed = topics.pop(topic_index)
    automation.topics = topics
    
    # Adjust current index if needed
    if automation.current_topic_index >= len(topics):
        automation.current_topic_index = 0
    
    db.commit()
    
    return {
        "success": True,
        "removed": removed,
        "topics": automation.topics,
        "total": len(automation.topics)
    }


@router.put("/{automation_id}/topics/reorder")
async def reorder_topics(
    automation_id: str,
    data: TopicsAdd,
    db: Session = Depends(get_db)
):
    """Replace all topics with a new ordered list."""
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    automation.topics = data.topics
    automation.current_topic_index = 0  # Reset index
    db.commit()
    
    return {
        "success": True,
        "topics": automation.topics,
        "total": len(automation.topics)
    }
