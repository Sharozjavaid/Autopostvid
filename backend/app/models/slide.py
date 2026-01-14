"""Slide model for individual slides within a project."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Slide(Base):
    """An individual slide within a project."""

    __tablename__ = "slides"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Content
    title = Column(Text, nullable=True)
    subtitle = Column(Text, nullable=True)
    visual_description = Column(Text, nullable=True)
    narration = Column(Text, nullable=True)  # For video-style content

    # Generated assets
    background_image_path = Column(String(500), nullable=True)
    final_image_path = Column(String(500), nullable=True)  # With text overlay
    video_clip_path = Column(String(500), nullable=True)

    # Current style settings
    current_font = Column(String(50), nullable=True, default="social")
    current_theme = Column(String(50), nullable=True, default="golden_dust")
    
    # Version tracking
    current_version = Column(Integer, default=0)  # Increments with each change

    # Status
    image_status = Column(String(50), default="pending")  # 'pending', 'generating', 'complete', 'error'
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="slides")
    versions = relationship("SlideVersion", back_populates="slide", cascade="all, delete-orphan", order_by="desc(SlideVersion.version_number)")

    def __repr__(self):
        return f"<Slide {self.order_index}: {self.title[:30] if self.title else 'Untitled'}>"
    
    def create_version(self, db, change_type: str, change_description: str = None, font: str = None, theme: str = None):
        """Create a new version snapshot of this slide."""
        from .slide_version import SlideVersion
        
        self.current_version += 1
        
        version = SlideVersion(
            slide_id=self.id,
            version_number=self.current_version,
            title=self.title,
            subtitle=self.subtitle,
            visual_description=self.visual_description,
            narration=self.narration,
            font=font or self.current_font,
            theme=theme or self.current_theme,
            background_image_path=self.background_image_path,
            final_image_path=self.final_image_path,
            change_type=change_type,
            change_description=change_description,
        )
        db.add(version)
        return version
