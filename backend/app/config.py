"""Application configuration using pydantic-settings."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "Philosophy Video Generator API"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./philosophy_generator.db"

    # API Keys
    google_api_key: str = ""
    elevenlabs_api_key: str = ""
    fal_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # File paths
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    generated_images_dir: Path = base_dir / "generated_images"
    generated_videos_dir: Path = base_dir / "generated_videos"
    generated_slides_dir: Path = base_dir / "generated_slides"

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
