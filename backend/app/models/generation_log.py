"""Generation log model for tracking costs and history."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from ..database import Base


class GenerationLog(Base):
    """Log entry for generation actions and costs."""

    __tablename__ = "generation_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    # Action details
    action = Column(String(100), nullable=False)  # 'script_generation', 'image_generation', etc.
    model_used = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)

    # Cost tracking
    cost = Column(Float, default=0.0)
    tokens_used = Column(Integer, nullable=True)

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="logs")

    def __repr__(self):
        return f"<GenerationLog {self.action} - ${self.cost:.4f}>"
