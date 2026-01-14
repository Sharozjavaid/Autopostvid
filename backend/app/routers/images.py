"""Images API router - Image generation for slides."""
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Slide
from ..schemas import ImageGenerateRequest, ImageGenerateResponse, ImageBatchGenerateRequest
from ..config import get_settings
from ..websocket.progress import manager
from ..services.prompt_config import get_image_prompt, IMAGE_STYLES

# Add parent dir to path for theme_config
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

router = APIRouter()
settings = get_settings()


def get_theme_config(theme_id: str):
    """Get theme configuration for image prompts."""
    try:
        from theme_config import get_theme, THEMES
        theme = get_theme(theme_id)
        if theme:
            return theme
        # Fall back to golden_dust
        return THEMES.get("golden_dust")
    except ImportError:
        return None


def get_image_generator(model: str = "gpt15"):
    """Get the appropriate image generator based on model."""
    if model == "gpt15":
        from ..services.gpt_image_generator import GPTImageGenerator
        return GPTImageGenerator()
    elif model == "flux":
        from ..services.smart_image_generator import SmartImageGenerator
        return SmartImageGenerator()
    else:
        from ..services.smart_image_generator import SmartImageGenerator
        return SmartImageGenerator()


def get_text_overlay():
    """Get TextOverlay class for programmatic text rendering."""
    from ..services.text_overlay import TextOverlay
    return TextOverlay(fonts_dir="fonts", default_style="modern")


async def generate_single_image(
    slide: Slide,
    model: str,
    font: str,
    db: Session,
    project_id: str = None,
    theme_id: str = "golden_dust"
) -> ImageGenerateResponse:
    """
    Generate background image and apply programmatic text overlay.
    
    This ALWAYS generates a clean background first, then adds text
    using Pillow for consistent, high-quality typography.
    
    The theme_id determines the visual style of the generated background.
    """
    try:
        slide.image_status = "generating"
        db.commit()

        # Broadcast progress
        if project_id:
            await manager.send_progress(project_id, {
                "type": "slide_generating",
                "slide_id": slide.id,
                "slide_index": slide.order_index,
                "message": f"Generating slide {slide.order_index + 1} with {theme_id} theme..."
            })

        generator = get_image_generator(model)

        # Get project for context
        project = db.query(Project).filter(Project.id == slide.project_id).first()
        story_title = project.name if project else "Philosophy"
        total_slides = len(project.slides) if project else 1

        # Determine slide type
        is_hook = slide.order_index == 0
        is_outro = slide.order_index == total_slides - 1

        # Get the image style from project settings or use default
        image_style = project.settings.get("image_style", "classical") if project.settings else "classical"

        # Build the visual prompt using the centralized prompt_config
        base_visual = slide.visual_description or "Dramatic philosophical scene"

        # Determine slide type for prompt
        if is_hook:
            slide_type = "hook"
        elif is_outro:
            slide_type = "outro"
        else:
            slide_type = "content"

        # Use the centralized get_image_prompt function
        # This prioritizes the visual description and applies the appropriate style
        if image_style in IMAGE_STYLES:
            visual_desc = get_image_prompt(
                visual_description=base_visual,
                image_style=image_style,
                slide_type=slide_type,
                content_type=project.script_style
            )
        else:
            # Fallback to legacy theme system
            theme = get_theme_config(theme_id)
            if theme:
                image_config = theme.image_config
                if is_hook:
                    theme_prompt = image_config.hook_prompt
                elif is_outro:
                    theme_prompt = image_config.outro_prompt
                else:
                    theme_prompt = image_config.content_prompt

                visual_desc = f"""PRIMARY SUBJECT (generate this exactly): {base_visual}

Apply {theme.name} aesthetic style to the subject above.
{theme_prompt}

AVOID: {image_config.negative_prompt}"""
            else:
                visual_desc = base_visual
        
        if model == "gpt15":
            background_path = generator.generate_background(
                visual_description=visual_desc,
                scene_number=slide.order_index + 1,
                story_title=story_title
            )
        else:
            # Other generators (flux, etc.)
            background_path = generator.generate_background(visual_desc)

        if not background_path:
            raise Exception("Background generation returned no result")

        slide.background_image_path = background_path

        # Apply programmatic text overlay using Pillow
        overlay = get_text_overlay()
        
        # Use theme's font if not overridden
        effective_font = font
        if font == "social" and theme:
            effective_font = theme.text_config.font_name
        
        # Ensure output directory exists
        settings.generated_slides_dir.mkdir(parents=True, exist_ok=True)
        final_path = str(settings.generated_slides_dir / f"{slide.id}_final.png")
        
        if is_hook:
            # Hook slide - just the main hook text
            overlay.create_hook_slide(
                background_path=background_path,
                output_path=final_path,
                hook_text=slide.subtitle or slide.title or story_title,
                font_name=effective_font,
                style="modern"
            )
        elif is_outro:
            # Outro slide - call to action
            overlay.create_outro_slide(
                background_path=background_path,
                output_path=final_path,
                text=slide.title or "YOUR CHOICE",
                subtitle=slide.subtitle,
                font_name=effective_font
            )
        else:
            # Content slide - with number, title, and subtitle
            overlay.create_slide(
                background_path=background_path,
                output_path=final_path,
                title=slide.title or "",
                subtitle=slide.subtitle or "",
                slide_number=slide.order_index,
                font_name=effective_font,
                style="modern"
            )
        
        # Determine change type for version
        is_regeneration = slide.final_image_path is not None
        change_type = "regenerate" if is_regeneration else "initial"
        change_desc = f"Generated with {effective_font} font and {theme_id} theme"
        if is_regeneration:
            change_desc = f"Regenerated with {effective_font} font and {theme_id} theme"
        
        # Create version snapshot
        version = slide.create_version(
            db=db,
            change_type=change_type,
            change_description=change_desc,
            font=effective_font,
            theme=theme_id
        )
        
        # Update slide
        slide.final_image_path = final_path
        slide.current_font = effective_font
        slide.current_theme = theme_id
        slide.image_status = "complete"
        slide.error_message = None
        db.commit()

        # Broadcast success
        if project_id:
            await manager.send_progress(project_id, {
                "type": "slide_complete",
                "slide_id": slide.id,
                "slide_index": slide.order_index,
                "image_url": f"/static/slides/{Path(slide.final_image_path).name}",
                "version": version.version_number
            })

        return ImageGenerateResponse(
            slide_id=slide.id,
            status="success",
            background_image_url=f"/static/images/{Path(background_path).name}",
            final_image_url=f"/static/slides/{Path(final_path).name}"
        )

    except Exception as e:
        slide.image_status = "error"
        slide.error_message = str(e)
        db.commit()

        if project_id:
            await manager.send_progress(project_id, {
                "type": "slide_error",
                "slide_id": slide.id,
                "slide_index": slide.order_index,
                "error": str(e)
            })

        return ImageGenerateResponse(
            slide_id=slide.id,
            status="error",
            error_message=str(e)
        )


@router.post("/generate/{slide_id}", response_model=ImageGenerateResponse)
async def generate_slide_image(
    slide_id: str,
    request: ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate image for a single slide."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    return await generate_single_image(
        slide=slide,
        model=request.model,
        font=request.font or "social",
        db=db,
        project_id=slide.project_id,
        theme_id=request.theme or "golden_dust"
    )


async def batch_generate_task(
    project_id: str,
    slide_ids: List[str],
    model: str,
    font: str,
    theme_id: str = "golden_dust"
):
    """Background task for batch image generation."""
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        await manager.send_progress(project_id, {
            "type": "batch_start",
            "total_slides": len(slide_ids),
            "theme": theme_id
        })

        for i, slide_id in enumerate(slide_ids):
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if slide:
                await generate_single_image(
                    slide=slide,
                    model=model,
                    font=font,
                    db=db,
                    project_id=project_id,
                    theme_id=theme_id
                )

            # Small delay between generations
            await asyncio.sleep(0.5)

        await manager.send_progress(project_id, {
            "type": "batch_complete",
            "total_generated": len(slide_ids)
        })

    finally:
        db.close()


@router.post("/generate-batch/{project_id}")
async def generate_batch_images(
    project_id: str,
    request: ImageBatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate images for multiple slides in batch."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get slides to generate
    if request.slide_ids:
        slides = db.query(Slide).filter(
            Slide.id.in_(request.slide_ids),
            Slide.project_id == project_id
        ).all()
    else:
        # Generate all pending slides
        slides = db.query(Slide).filter(
            Slide.project_id == project_id,
            Slide.image_status.in_(["pending", "error"])
        ).order_by(Slide.order_index).all()

    if not slides:
        return {"message": "No slides to generate", "total": 0}

    slide_ids = [s.id for s in slides]

    # Update project status
    project.status = "generating"
    db.commit()

    # Start background task
    background_tasks.add_task(
        batch_generate_task,
        project_id,
        slide_ids,
        request.model,
        request.font or "social",
        request.theme or "golden_dust"
    )

    return {
        "message": "Batch generation started",
        "project_id": project_id,
        "total_slides": len(slides),
        "status": "generating"
    }


@router.get("/{slide_id}")
async def get_slide_image(slide_id: str, db: Session = Depends(get_db)):
    """Get image URLs for a slide."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    return {
        "slide_id": slide.id,
        "status": slide.image_status,
        "background_image": f"/static/images/{Path(slide.background_image_path).name}" if slide.background_image_path else None,
        "final_image": f"/static/slides/{Path(slide.final_image_path).name}" if slide.final_image_path else None
    }


@router.post("/{slide_id}/reapply-text")
async def reapply_text_overlay(
    slide_id: str,
    font: str = "social",
    db: Session = Depends(get_db)
):
    """
    Re-apply text overlay to existing background with a new font.
    
    This is FAST because it reuses the existing background image
    and only re-renders the text with a different font.
    No AI image generation is needed.
    
    If no separate background exists, falls back to using the final image
    as the background (text will be re-rendered on top).
    """
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    
    # Try to find a usable background image
    background_path = None
    
    # First choice: dedicated background image
    if slide.background_image_path and os.path.exists(slide.background_image_path):
        background_path = slide.background_image_path
    # Fallback: use final image as background (will re-render text on top)
    elif slide.final_image_path and os.path.exists(slide.final_image_path):
        background_path = slide.final_image_path
    
    if not background_path:
        raise HTTPException(
            status_code=400, 
            detail="No image exists. Generate an image first."
        )
    
    try:
        # Get project for context
        project = db.query(Project).filter(Project.id == slide.project_id).first()
        total_slides = len(project.slides) if project else 1
        story_title = project.name if project else "Philosophy"
        
        # Determine slide type
        is_hook = slide.order_index == 0
        is_outro = slide.order_index == total_slides - 1
        
        # Get text overlay
        overlay = get_text_overlay()
        
        # Create new output path
        settings.generated_slides_dir.mkdir(parents=True, exist_ok=True)
        final_path = str(settings.generated_slides_dir / f"{slide.id}_final.png")
        
        if is_hook:
            overlay.create_hook_slide(
                background_path=background_path,
                output_path=final_path,
                hook_text=slide.subtitle or slide.title or story_title,
                font_name=font,
                style="modern"
            )
        elif is_outro:
            overlay.create_outro_slide(
                background_path=background_path,
                output_path=final_path,
                text=slide.title or "YOUR CHOICE",
                subtitle=slide.subtitle,
                font_name=font
            )
        else:
            overlay.create_slide(
                background_path=background_path,
                output_path=final_path,
                title=slide.title or "",
                subtitle=slide.subtitle or "",
                slide_number=slide.order_index,
                font_name=font,
                style="modern"
            )
        
        # Store previous font for version description
        old_font = slide.current_font or "unknown"
        
        # Create a version snapshot before updating
        version = slide.create_version(
            db=db,
            change_type="font_change",
            change_description=f"Changed font from {old_font} to {font}",
            font=font,
            theme=slide.current_theme
        )
        
        # Update slide with new values
        slide.final_image_path = final_path
        slide.current_font = font
        slide.image_status = "complete"
        slide.error_message = None
        db.commit()
        
        return {
            "success": True,
            "slide_id": slide.id,
            "font": font,
            "final_image_url": f"/static/slides/{Path(final_path).name}",
            "message": f"Text re-applied with {font} font",
            "version": version.version_number
        }
        
    except Exception as e:
        slide.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slide_id}/versions")
async def get_slide_versions(slide_id: str, db: Session = Depends(get_db)):
    """Get all version history for a slide."""
    from ..models import SlideVersion
    
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    
    versions = db.query(SlideVersion).filter(
        SlideVersion.slide_id == slide_id
    ).order_by(SlideVersion.version_number.desc()).all()
    
    return {
        "slide_id": slide_id,
        "current_version": slide.current_version,
        "total_versions": len(versions),
        "versions": [v.to_dict() for v in versions]
    }


@router.post("/{slide_id}/revert/{version_number}")
async def revert_to_version(
    slide_id: str, 
    version_number: int, 
    db: Session = Depends(get_db)
):
    """Revert a slide to a previous version."""
    from ..models import SlideVersion
    
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    
    version = db.query(SlideVersion).filter(
        SlideVersion.slide_id == slide_id,
        SlideVersion.version_number == version_number
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
    
    # Check if the version's image still exists
    if version.final_image_path and os.path.exists(version.final_image_path):
        # Create a new version marking the revert
        revert_version = slide.create_version(
            db=db,
            change_type="revert",
            change_description=f"Reverted to version {version_number}",
            font=version.font,
            theme=version.theme
        )
        
        # Restore the slide content from the version
        slide.title = version.title
        slide.subtitle = version.subtitle
        slide.visual_description = version.visual_description
        slide.narration = version.narration
        slide.current_font = version.font
        slide.current_theme = version.theme
        slide.final_image_path = version.final_image_path
        slide.background_image_path = version.background_image_path
        slide.image_status = "complete"
        db.commit()
        
        return {
            "success": True,
            "message": f"Reverted to version {version_number}",
            "slide_id": slide_id,
            "new_version": revert_version.version_number
        }
    else:
        raise HTTPException(
            status_code=400, 
            detail="Cannot revert - version's image file no longer exists"
        )


@router.delete("/{slide_id}/image")
async def delete_slide_image(slide_id: str, db: Session = Depends(get_db)):
    """Delete generated images for a slide and reset status."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    # Delete files if they exist
    if slide.background_image_path and os.path.exists(slide.background_image_path):
        os.remove(slide.background_image_path)
    if slide.final_image_path and os.path.exists(slide.final_image_path):
        os.remove(slide.final_image_path)

    slide.background_image_path = None
    slide.final_image_path = None
    slide.image_status = "pending"
    slide.error_message = None
    db.commit()

    return {"success": True, "message": "Image deleted, slide reset to pending"}
