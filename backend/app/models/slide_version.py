"""SlideVersion model for tracking edit history of slides."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class SlideVersion(Base):
    """A version snapshot of a slide, tracking all edits and regenerations."""

    __tablename__ = "slide_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slide_id = Column(String(36), ForeignKey("slides.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)

    # Content at this version
    title = Column(Text, nullable=True)
    subtitle = Column(Text, nullable=True)
    visual_description = Column(Text, nullable=True)
    narration = Column(Text, nullable=True)

    # Style settings used
    font = Column(String(50), nullable=True)
    theme = Column(String(50), nullable=True)
    
    # Generated assets for this version
    background_image_path = Column(String(500), nullable=True)
    final_image_path = Column(String(500), nullable=True)
    
    # What changed in this version
    change_type = Column(String(50), nullable=False)  # 'initial', 'text_edit', 'font_change', 'theme_change', 'regenerate', 'full_regenerate'
    change_description = Column(Text, nullable=True)  # Human-readable description
    
    # Additional metadata (for extensibility)
    version_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    slide = relationship("Slide", back_populates="versions")

    def __repr__(self):
        return f"<SlideVersion v{self.version_number} ({self.change_type}): {self.slide_id[:8]}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "slide_id": self.slide_id,
            "version_number": self.version_number,
            "title": self.title,
            "subtitle": self.subtitle,
            "visual_description": self.visual_description,
            "narration": self.narration,
            "font": self.font,
            "theme": self.theme,
            "background_image_path": self.background_image_path,
            "final_image_path": self.final_image_path,
            "change_type": self.change_type,
            "change_description": self.change_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
