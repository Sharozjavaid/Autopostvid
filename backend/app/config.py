"""Application configuration using pydantic-settings."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path


# =============================================================================
# CLAUDE MODEL CONFIGURATION
# =============================================================================
# Single source of truth for Claude model used across the application.
# Change this ONE variable to switch models everywhere.
#
# Available models for prompt caching:
# - claude-sonnet-4-5-20250929 (recommended - best price/performance)
# - claude-opus-4-20250514 (most capable, expensive)
# - claude-haiku-3-5-20241022 (fastest/cheapest)
# =============================================================================
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Max tokens for Claude responses
CLAUDE_MAX_TOKENS = 16384

# Max tool call iterations per request
CLAUDE_MAX_ITERATIONS = 25


# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================
def is_production() -> bool:
    """Detect if running in production (GCP VM/Docker) vs local development."""
    # Check for explicit environment variable first (set by Docker)
    env = os.environ.get("ENVIRONMENT", "").lower()
    if env in ("production", "prod"):
        return True
    if env in ("development", "dev", "local"):
        return False
    
    # Check for GCS credentials (indicates production)
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    
    # Check for Docker environment (running inside container)
    docker_app = Path("/app")
    if docker_app.exists() and (docker_app / "backend").exists():
        return True
    
    # Auto-detect: Check if running on GCP VM directly
    gcp_path = Path("/home/runner/philosophy_video_generator")
    if gcp_path.exists():
        return True
    
    # Default to development
    return False


# Export for use in other modules
IS_PRODUCTION = is_production()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "Philosophy Video Generator API"
    debug: bool = not IS_PRODUCTION  # Debug off in production

    # Database
    database_url: str = "sqlite:///./philosophy_generator.db"

    # API Keys
    google_api_key: str = ""
    elevenlabs_api_key: str = ""
    fal_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # File paths - resolve base_dir dynamically to work in both local and Docker
    # Local: backend/app/config.py -> 4 parents -> philosophy_video_generator/
    # Docker: /app/backend/app/config.py -> 3 parents -> /app/
    @property
    def base_dir(self) -> Path:
        # Check for Docker environment (/app as root)
        docker_app = Path("/app")
        if docker_app.exists() and (docker_app / "backend").exists():
            return docker_app
        # Local development - 4 parents from this file
        return Path(__file__).parent.parent.parent.parent

    @property
    def generated_images_dir(self) -> Path:
        return self.base_dir / "generated_images"
    
    @property
    def generated_videos_dir(self) -> Path:
        return self.base_dir / "generated_videos"
    
    @property
    def generated_slides_dir(self) -> Path:
        return self.base_dir / "generated_slides"

    # CORS - allow localhost for dev, Vercel for production
    cors_origins: list[str] = [
        # Local development
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        # Production - Vercel
        "https://app.cofndrly.com",
        "https://frontend-lyart-ten-67.vercel.app",
        "https://*.vercel.app",
        # GCP VM direct
        "http://23.251.149.244:8501",
        "http://23.251.149.244:8001",
        "http://23.251.149.244",
        "*",  # Allow all origins for now (can restrict later)
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
