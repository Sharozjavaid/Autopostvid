"""Project model for video/slideshow projects."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.orm import relationship
from ..database import Base


class Project(Base):
    """A video or slideshow project."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    topic = Column(Text, nullable=True)
    content_type = Column(String(50), default="slideshow")  # 'slideshow' or 'video'
    script_style = Column(String(50), default="list")  # 'list', 'narrative', 'mentor_slideshow'
    status = Column(String(50), default="draft")  # 'draft', 'script_review', 'script_approved', 'generating', 'complete', 'error'
    script_approved = Column(String(1), default="N")  # 'Y' or 'N' - whether user approved the script

    # Settings stored as JSON
    settings = Column(JSON, default=dict)
    # Example settings:
    # {
    #   "image_model": "gpt15",
    #   "font": "bebas",
    #   "theme": "dark",
    #   "voice_id": "..."
    # }

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    slides = relationship("Slide", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("GenerationLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name} ({self.status})>"
