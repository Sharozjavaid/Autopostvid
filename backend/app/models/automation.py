"""Automation model for scheduled content generation."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer
from ..database import Base


class Automation(Base):
    """Scheduled automation configuration for philosophical slideshows.

    This model stores "recipes" that can automatically generate slideshows:
    - Content type determines script structure (list_educational, wisdom_slideshow, etc.)
    - Image style determines visual aesthetic (classical, surreal, cinematic, minimal)
    - Topics queue is a list of topics to cycle through
    - Schedule times define when to run (e.g., ["09:00", "18:00"])
    - Email settings for notifications when slideshows are ready
    """

    __tablename__ = "automations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)

    # Content Configuration
    content_type = Column(String(50), default="wisdom_slideshow")
    # Options: list_educational, list_existential, wisdom_slideshow, narrative_story

    image_style = Column(String(50), default="classical")
    # Options: classical, surreal, cinematic, minimal

    # Topics Queue - JSON array of topics to cycle through
    topics = Column(JSON, default=list)
    # Example: ["5 Stoic philosophers", "Why anxiety is useful", "The trap of happiness"]

    current_topic_index = Column(Integer, default=0)
    # Tracks which topic to use next

    # Schedule Configuration
    schedule_times = Column(JSON, default=list)
    # Array of times in 24hr format: ["09:00", "14:00", "21:00"]

    schedule_days = Column(JSON, default=list)
    # Days of week: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    # Empty = every day

    # Email Notification Settings
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(255), nullable=True)
    email_on_complete = Column(Boolean, default=True)  # Email when slideshow is ready
    email_on_error = Column(Boolean, default=True)  # Email on failures

    # Additional Settings (JSON for flexibility)
    settings = Column(JSON, default=dict)
    # Example: {
    #   "auto_approve_script": true,
    #   "auto_generate_images": true,
    #   "image_model": "gpt15",
    #   "font": "social"
    # }

    # State
    status = Column(String(50), default="stopped")  # 'running', 'paused', 'stopped'
    is_active = Column(Boolean, default=False)
    process_id = Column(Integer, nullable=True)

    # Timing
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Legacy config field for backwards compatibility
    config = Column(JSON, default=dict)

    def __repr__(self):
        return f"<Automation {self.name} ({self.status})>"

    def get_next_topic(self) -> str:
        """Get the next topic from the queue and advance the index."""
        if not self.topics:
            return "Philosophy and life"

        topic = self.topics[self.current_topic_index % len(self.topics)]
        return topic

    def advance_topic(self):
        """Move to the next topic in the queue."""
        if self.topics:
            self.current_topic_index = (self.current_topic_index + 1) % len(self.topics)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "content_type": self.content_type,
            "image_style": self.image_style,
            "topics": self.topics or [],
            "current_topic_index": self.current_topic_index,
            "schedule_times": self.schedule_times or [],
            "schedule_days": self.schedule_days or [],
            "email_enabled": self.email_enabled,
            "email_address": self.email_address,
            "email_on_complete": self.email_on_complete,
            "email_on_error": self.email_on_error,
            "settings": self.settings or {},
            "status": self.status,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
