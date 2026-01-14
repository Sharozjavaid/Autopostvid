"""FastAPI main application entry point."""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routers import projects, scripts, slides, images, automations, tiktok, agent, gallery, inspiration
from .websocket.progress import router as ws_router

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("Starting Philosophy Video Generator API...")
    init_db()

    # Ensure directories exist
    settings.generated_images_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_videos_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_slides_dir.mkdir(parents=True, exist_ok=True)

    # Start the automation scheduler
    try:
        from .services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("Automation scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    yield

    # Shutdown
    print("Shutting down...")
    
    # Stop the scheduler
    try:
        from .services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("Automation scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


app = FastAPI(
    title=settings.app_name,
    description="API for generating philosophy video content with AI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated content
if settings.generated_images_dir.exists():
    app.mount(
        "/static/images",
        StaticFiles(directory=str(settings.generated_images_dir)),
        name="images"
    )

if settings.generated_slides_dir.exists():
    app.mount(
        "/static/slides",
        StaticFiles(directory=str(settings.generated_slides_dir)),
        name="slides"
    )

# Mount static files for automation-generated slideshows
# These are stored in generated_slideshows/gpt15/, generated_slideshows/flux/, etc.
generated_slideshows_dir = settings.base_dir / "generated_slideshows"
if generated_slideshows_dir.exists():
    app.mount(
        "/static/slideshows",
        StaticFiles(directory=str(generated_slideshows_dir)),
        name="slideshows"
    )

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(slides.router, prefix="/api/slides", tags=["slides"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(automations.router, prefix="/api/automations", tags=["automations"])
app.include_router(tiktok.router, prefix="/api/tiktok", tags=["tiktok"])
app.include_router(agent.router, tags=["agent"])  # Agent router (already has /api/agent prefix)
app.include_router(gallery.router, tags=["gallery"])  # Gallery router (already has /api/gallery prefix)
app.include_router(inspiration.router, tags=["inspiration"])  # Inspiration/reference library
app.include_router(ws_router, tags=["websocket"])

# Mount references directory for inspiration frames
references_dir = settings.base_dir / "references" / "examples"
if references_dir.exists():
    app.mount(
        "/static/references",
        StaticFiles(directory=str(references_dir)),
        name="references"
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "gemini": bool(settings.google_api_key),
            "elevenlabs": bool(settings.elevenlabs_api_key),
            "fal": bool(settings.fal_key),
            "openai": bool(settings.openai_api_key)
        }
    }


@app.get("/api/settings/models")
async def get_available_models():
    """Get available image and voice models."""
    return {
        "image_models": [
            {"id": "gpt15", "name": "GPT Image 1.5", "provider": "fal.ai"},
            {"id": "flux", "name": "Flux Schnell", "provider": "fal.ai"},
            {"id": "dalle3", "name": "DALL-E 3", "provider": "OpenAI"}
        ],
        "fonts": [
            {"id": "tiktok", "name": "TikTok Sans", "style": "Official TikTok Font, Clean & Modern"},
            {"id": "tiktok-bold", "name": "TikTok Sans Bold", "style": "Official TikTok Display Font"},
            {"id": "social", "name": "Social (Default)", "style": "Clean, Readable, Sentence Case", "default": True},
            {"id": "bebas", "name": "Bebas Neue", "style": "Bold, Impact, All-Caps"},
            {"id": "montserrat", "name": "Montserrat", "style": "Modern, Clean"},
            {"id": "cinzel", "name": "Cinzel", "style": "Classical, Roman"},
            {"id": "oswald", "name": "Oswald", "style": "Condensed, Strong"},
            {"id": "cormorant", "name": "Cormorant", "style": "Elegant, Serif Italic"}
        ],
        "themes": [
            {"id": "dark", "name": "Dark Mode"},
            {"id": "golden", "name": "Golden Classical"},
            {"id": "marble", "name": "Marble & Stone"},
            {"id": "minimal", "name": "Minimal White"}
        ]
    }
