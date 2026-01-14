"""GalleryItem model for storing all assets created during agent sessions."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from ..database import Base


class GalleryItem(Base):
    """
    Stores all assets created during agent sessions - slides, scripts, images, etc.
    This provides a persistent history of everything the user has created,
    whether complete or in-progress.
    """

    __tablename__ = "gallery_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Type of asset: 'slide', 'script', 'prompt', 'image', 'project'
    item_type = Column(String(50), nullable=False, default="slide")
    
    # Reference to source (optional - for slides that belong to projects)
    project_id = Column(String(36), nullable=True)
    slide_id = Column(String(36), nullable=True)
    
    # Display info
    title = Column(String(255), nullable=True)
    subtitle = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Asset content
    image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    
    # For scripts/prompts - store the text content
    text_content = Column(Text, nullable=True)
    
    # Style metadata
    font = Column(String(50), nullable=True)
    theme = Column(String(50), nullable=True)
    content_style = Column(String(50), nullable=True)  # mentor, wisdom_thread, etc.
    
    # Additional extra_data as JSON (metadata is reserved by SQLAlchemy)
    extra_data = Column(JSON, nullable=True)
    
    # Status: 'complete', 'draft', 'failed'
    status = Column(String(50), default="complete")
    
    # Session tracking
    session_id = Column(String(36), nullable=True)  # Links to agent session
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GalleryItem {self.item_type}: {self.title[:30] if self.title else 'Untitled'}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "item_type": self.item_type,
            "project_id": self.project_id,
            "slide_id": self.slide_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "text_content": self.text_content,
            "font": self.font,
            "theme": self.theme,
            "content_style": self.content_style,
            "metadata": self.extra_data,
            "status": self.status,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
