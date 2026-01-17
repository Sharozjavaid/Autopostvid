"""FastAPI main application entry point."""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings, IS_PRODUCTION
from .database import init_db
from .routers import projects, scripts, slides, images, automations, tiktok, agent, gallery, inspiration, storage, video
from .websocket.progress import router as ws_router
from .middleware import (
    verify_api_key,
    limiter,
    rate_limit_exceeded_handler,
    register_error_handlers,
    SecurityHeadersMiddleware,
)

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("Starting Philosophy Video Generator API...")
    
    # Log security status
    if settings.api_key:
        logger.info("API key authentication ENABLED")
    else:
        logger.warning("API key authentication DISABLED - set API_KEY in .env for production")
    
    if IS_PRODUCTION:
        logger.info("Running in PRODUCTION mode")
    else:
        logger.info("Running in DEVELOPMENT mode")
    
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


# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = FastAPI(
    title=settings.app_name,
    description="API for generating philosophy video content with AI",
    version="2.0.0",
    lifespan=lifespan,
    # Disable docs in production for security
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None,
)

# =============================================================================
# SECURITY MIDDLEWARE (order matters - first added = last executed)
# =============================================================================

# 1. Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Global error handlers
register_error_handlers(app)

# =============================================================================
# STATIC FILE MOUNTS
# =============================================================================

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
generated_slideshows_dir = settings.base_dir / "generated_slideshows"
if generated_slideshows_dir.exists():
    app.mount(
        "/static/slideshows",
        StaticFiles(directory=str(generated_slideshows_dir)),
        name="slideshows"
    )

# Mount references directory for inspiration frames
references_dir = settings.base_dir / "references" / "examples"
if references_dir.exists():
    app.mount(
        "/static/references",
        StaticFiles(directory=str(references_dir)),
        name="references"
    )

# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

# All routers require API key authentication
# The verify_api_key dependency returns early if API_KEY is not configured
protected_routes = [Depends(verify_api_key)]

app.include_router(
    projects.router, 
    prefix="/api/projects", 
    tags=["projects"],
    dependencies=protected_routes
)
app.include_router(
    scripts.router, 
    prefix="/api/scripts", 
    tags=["scripts"],
    dependencies=protected_routes
)
app.include_router(
    slides.router, 
    prefix="/api/slides", 
    tags=["slides"],
    dependencies=protected_routes
)
app.include_router(
    images.router, 
    prefix="/api/images", 
    tags=["images"],
    dependencies=protected_routes
)
app.include_router(
    automations.router, 
    prefix="/api/automations", 
    tags=["automations"],
    dependencies=protected_routes
)
app.include_router(
    tiktok.router, 
    prefix="/api/tiktok", 
    tags=["tiktok"],
    dependencies=protected_routes
)
# Public TikTok media endpoint - NO AUTH required (TikTok needs to fetch images)
app.include_router(
    tiktok.public_router, 
    prefix="/api/tiktok", 
    tags=["tiktok-public"]
)
app.include_router(
    agent.router, 
    tags=["agent"],
    dependencies=protected_routes
)
app.include_router(
    gallery.router, 
    tags=["gallery"],
    dependencies=protected_routes
)
app.include_router(
    inspiration.router, 
    tags=["inspiration"],
    dependencies=protected_routes
)
app.include_router(
    storage.router, 
    tags=["storage"],
    dependencies=protected_routes
)
app.include_router(
    video.router, 
    tags=["video"],
    dependencies=protected_routes
)
app.include_router(ws_router, tags=["websocket"])  # WebSocket doesn't use HTTP auth


# =============================================================================
# PUBLIC ENDPOINTS (no authentication required)
# =============================================================================

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """Health check endpoint - public."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "2.0.0"
    }


@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Health check endpoint - public.
    
    Note: In production, we don't expose which API keys are configured
    to prevent information disclosure.
    """
    if IS_PRODUCTION:
        return {"status": "healthy"}
    
    # Development mode - show service status
    return {
        "status": "healthy",
        "database": "connected",
        "auth_enabled": bool(settings.api_key),
        "services": {
            "gemini": bool(settings.google_api_key),
            "elevenlabs": bool(settings.elevenlabs_api_key),
            "fal": bool(settings.fal_key),
            "openai": bool(settings.openai_api_key)
        }
    }


@app.get("/api/settings/models")
@limiter.limit("100/minute")
async def get_available_models(request: Request):
    """Get available image and voice models - public."""
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


# =============================================================================
# PROTECTED ENDPOINTS (require API key)
# =============================================================================

@app.get("/api/storage/stats", dependencies=protected_routes)
@limiter.limit("30/minute")
async def get_storage_stats(request: Request):
    """Get cloud storage statistics - PROTECTED."""
    from .services.cloud_storage import get_storage_service
    
    storage = get_storage_service()
    stats = storage.get_storage_stats()
    
    return stats


@app.get("/api/storage/list/{folder}", dependencies=protected_routes)
@limiter.limit("30/minute")
async def list_storage_folder(request: Request, folder: str, limit: int = 50):
    """List files in a specific storage folder - PROTECTED."""
    from .services.cloud_storage import get_storage_service
    
    storage = get_storage_service()
    if not storage.is_available:
        return {"error": "Cloud storage not configured", "files": []}
    
    files = storage.list_files(prefix=folder)
    return {
        "folder": folder,
        "total": len(files),
        "files": files[:limit]
    }
