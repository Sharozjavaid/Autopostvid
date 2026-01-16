"""Automation run history model for tracking each execution."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class AutomationRun(Base):
    """Individual automation run record.
    
    Tracks each time an automation executes:
    - What topic was used
    - Whether it succeeded or failed
    - TikTok post status
    - Generated content paths
    """
    
    __tablename__ = "automation_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    automation_id = Column(String(36), ForeignKey("automations.id"), nullable=False)
    
    # Run details
    topic = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, posted
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Generated content
    project_id = Column(String(36), nullable=True)  # If saved to projects
    slides_count = Column(Integer, default=0)
    image_paths = Column(JSON, default=list)  # List of generated image paths
    script_path = Column(String(500), nullable=True)
    
    # TikTok posting
    tiktok_posted = Column(Boolean, default=False)
    tiktok_publish_id = Column(String(100), nullable=True)
    tiktok_post_status = Column(String(50), nullable=True)  # pending, processing, success, failed
    tiktok_error = Column(Text, nullable=True)
    
    # Instagram posting
    instagram_posted = Column(Boolean, default=False)
    instagram_post_id = Column(String(100), nullable=True)
    instagram_post_status = Column(String(50), nullable=True)  # pending, posted, failed
    instagram_error = Column(Text, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Metadata
    settings_used = Column(JSON, default=dict)  # Snapshot of settings at run time
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AutomationRun {self.id[:8]} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "automation_id": self.automation_id,
            "topic": self.topic,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "project_id": self.project_id,
            "slides_count": self.slides_count,
            "image_paths": self.image_paths or [],
            "script_path": self.script_path,
            "tiktok_posted": self.tiktok_posted,
            "tiktok_publish_id": self.tiktok_publish_id,
            "tiktok_post_status": self.tiktok_post_status,
            "tiktok_error": self.tiktok_error,
            "instagram_posted": self.instagram_posted,
            "instagram_post_id": self.instagram_post_id,
            "instagram_post_status": self.instagram_post_status,
            "instagram_error": self.instagram_error,
            "error_message": self.error_message,
            "settings_used": self.settings_used or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def mark_completed(self, slides_count: int = 0, image_paths: list = None):
        """Mark run as completed successfully."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.slides_count = slides_count
        self.image_paths = image_paths or []
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    def mark_failed(self, error_message: str, error_details: dict = None):
        """Mark run as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    def mark_posted(self, publish_id: str):
        """Mark as posted to TikTok."""
        self.tiktok_posted = True
        self.tiktok_publish_id = publish_id
        self.tiktok_post_status = "pending"  # TikTok processing
        self.status = "posted"
