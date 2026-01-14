"""Scripts API router - Script generation for projects."""
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Slide
from ..schemas import ScriptGenerateRequest, ScriptGenerateResponse, ScriptSlide
from ..services.prompt_config import (
    list_content_types,
    list_image_styles,
    get_content_type_config,
    CONTENT_TYPES,
)

# Add services to path
services_path = Path(__file__).parent.parent / "services"
sys.path.insert(0, str(services_path))

router = APIRouter()


def get_gemini_handler():
    """Lazy load GeminiHandler to avoid import issues."""
    from ..services.gemini_handler import GeminiHandler
    return GeminiHandler()


@router.post("/generate", response_model=ScriptGenerateResponse)
async def generate_script_endpoint(
    request: ScriptGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate a script from a topic and create a project with slides in review mode."""
    try:
        handler = get_gemini_handler()

        # Determine content type
        content_type = request.content_type
        if content_type == "auto" or content_type is None:
            # Default to wisdom_slideshow if not specified
            content_type = "wisdom_slideshow"

        # Get config for this content type
        config = get_content_type_config(content_type)
        # Use provided image_style or fall back to content type's default
        image_style = request.image_style if hasattr(request, 'image_style') and request.image_style else None
        if not image_style:
            image_style = config.default_image_style if config else "classical"

        # Use the new unified generate_script method if available for new content types
        if content_type in CONTENT_TYPES:
            # Enhance topic for better results
            enhanced_topic = handler.enhance_topic_prompt(request.topic)
            result = handler.generate_script(enhanced_topic, content_type)
        # Fallback to legacy methods for old content types
        elif content_type == "mentor_slideshow":
            result = handler.generate_mentor_slideshow(request.topic)
        elif content_type == "list":
            result = handler._generate_list_content(
                request.topic,
                num_scenes=request.num_slides or 7
            )
        else:
            result = handler._generate_narrative_story(
                request.topic,
                num_scenes=request.num_slides or 10
            )

        if not result:
            raise HTTPException(status_code=500, detail="Script generation returned no result")

        # Create project in script_review status (not approved yet)
        # Store image_style in settings
        project = Project(
            name=request.topic[:100],
            topic=request.topic,
            content_type="slideshow",
            script_style=content_type,
            status="script_review",
            script_approved="N",
            settings={"image_style": image_style}
        )
        db.add(project)
        db.flush()

        # Create slides from script
        slides = []
        scenes = result.get("scenes", result.get("slides", []))

        for i, scene in enumerate(scenes):
            # Handle different format structures
            title = scene.get("title", scene.get("hook", scene.get("display_text", "")))
            subtitle = scene.get("subtitle", scene.get("text", scene.get("content", "")))
            visual = scene.get("visual_description", scene.get("visual", ""))
            narration = scene.get("narration", scene.get("script", ""))

            slide = Slide(
                project_id=project.id,
                order_index=i,
                title=title,
                subtitle=subtitle,
                visual_description=visual,
                narration=narration
            )
            db.add(slide)
            slides.append(ScriptSlide(
                title=slide.title or "",
                subtitle=slide.subtitle,
                visual_description=slide.visual_description or "",
                narration=slide.narration
            ))

        db.commit()

        return ScriptGenerateResponse(
            project_id=project.id,
            topic=request.topic,
            content_type=content_type,
            slides=slides,
            total_slides=len(slides)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@router.post("/{project_id}/regenerate-slide/{slide_index}")
async def regenerate_slide_script(
    project_id: str,
    slide_index: int,
    instruction: str = None,
    db: Session = Depends(get_db)
):
    """Regenerate the script for a specific slide."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    slide = db.query(Slide).filter(
        Slide.project_id == project_id,
        Slide.order_index == slide_index
    ).first()

    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    try:
        handler = get_gemini_handler()

        prompt = f"""
        Regenerate this slide for the topic: {project.topic}

        Current content:
        - Title: {slide.title}
        - Subtitle: {slide.subtitle}
        - Visual: {slide.visual_description}

        {f"Special instruction: {instruction}" if instruction else "Make it more engaging and impactful."}

        Return JSON with: title, subtitle, visual_description
        """

        # Use Gemini to regenerate
        response = handler.client.models.generate_content(
            model=handler.text_model_name,
            contents=prompt
        )

        import json
        result = json.loads(handler._clean_json_text(response.text))

        slide.title = result.get("title", slide.title)
        slide.subtitle = result.get("subtitle", slide.subtitle)
        slide.visual_description = result.get("visual_description", slide.visual_description)
        slide.image_status = "pending"  # Reset for regeneration

        db.commit()

        return {
            "success": True,
            "slide": {
                "id": slide.id,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "visual_description": slide.visual_description
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.put("/{project_id}/slides/{slide_id}")
async def update_slide_script(
    project_id: str,
    slide_id: str,
    title: str = None,
    subtitle: str = None,
    visual_description: str = None,
    narration: str = None,
    db: Session = Depends(get_db)
):
    """Manually update a slide's script content."""
    slide = db.query(Slide).filter(
        Slide.id == slide_id,
        Slide.project_id == project_id
    ).first()

    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    if title is not None:
        slide.title = title
    if subtitle is not None:
        slide.subtitle = subtitle
    if visual_description is not None:
        slide.visual_description = visual_description
        slide.image_status = "pending"  # Reset if visual changed
    if narration is not None:
        slide.narration = narration

    db.commit()

    return {
        "success": True,
        "slide": {
            "id": slide.id,
            "title": slide.title,
            "subtitle": slide.subtitle,
            "visual_description": slide.visual_description,
            "narration": slide.narration
        }
    }


@router.post("/{project_id}/approve")
async def approve_script(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Approve the script and allow image generation to proceed."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.script_approved = "Y"
    project.status = "script_approved"
    db.commit()
    
    return {
        "success": True,
        "message": "Script approved. You can now generate images.",
        "project_id": project.id
    }


@router.post("/{project_id}/regenerate-all")
async def regenerate_entire_script(
    project_id: str,
    new_style: str = None,
    db: Session = Depends(get_db)
):
    """Regenerate the entire script with optionally a different style."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        handler = get_gemini_handler()
        
        # Use new style or keep current
        content_type = new_style if new_style else project.script_style
        
        # Generate script based on content type
        if content_type == "wisdom_slideshow":
            enhanced_topic = handler.enhance_topic_prompt(project.topic)
            result = handler.generate_wisdom_slideshow(enhanced_topic)
        elif content_type == "mentor_slideshow":
            result = handler.generate_mentor_slideshow(project.topic)
        elif content_type == "list":
            num_slides = len(project.slides) if project.slides else 7
            result = handler._generate_list_content(project.topic, num_scenes=num_slides)
        else:
            num_slides = len(project.slides) if project.slides else 10
            result = handler._generate_narrative_story(project.topic, num_scenes=num_slides)
        
        # Delete old slides
        for slide in project.slides:
            db.delete(slide)

        # Create new slides
        scenes = result.get("scenes", result.get("slides", []))
        for i, scene in enumerate(scenes):
            # Handle different format structures (wisdom_slideshow uses 'content', others use 'text')
            title = scene.get("title", scene.get("hook", scene.get("display_text", "")))
            subtitle = scene.get("subtitle", scene.get("text", scene.get("content", "")))
            visual = scene.get("visual_description", scene.get("visual", ""))
            narration = scene.get("narration", scene.get("script", ""))

            slide = Slide(
                project_id=project.id,
                order_index=i,
                title=title,
                subtitle=subtitle,
                visual_description=visual,
                narration=narration
            )
            db.add(slide)
        
        # Update project style and reset approval
        project.script_style = content_type
        project.script_approved = "N"
        project.status = "script_review"
        
        db.commit()
        db.refresh(project)
        
        return {
            "success": True,
            "message": "Script regenerated successfully",
            "content_type": content_type,
            "total_slides": len(scenes)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script regeneration failed: {str(e)}")


@router.get("/styles")
async def get_script_styles():
    """Get available script generation styles (legacy endpoint)."""
    # Use the new centralized content types
    return {"styles": list_content_types()}


@router.get("/content-types")
async def get_content_types():
    """Get all available content types with their configurations."""
    return {
        "content_types": list_content_types()
    }


@router.get("/image-styles")
async def get_image_styles():
    """Get all available image styles."""
    return {
        "image_styles": list_image_styles()
    }
