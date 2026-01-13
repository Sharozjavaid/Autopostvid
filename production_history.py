#!/usr/bin/env python3
"""
Production History - Track all generated content with full metadata.

Stores:
- Date/time generated
- Content type (slideshow, narration, video_transitions)
- Topic and title
- Image model used
- Font/style settings
- File paths
- Cost estimate
- Pipeline configuration

Used by the Streamlit dashboard to display production history.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

# History file
HISTORY_FILE = "production_history.json"


@dataclass
class ProductionRecord:
    """A single production record."""
    id: str
    timestamp: str
    date: str  # YYYY-MM-DD for easy filtering
    
    # Content info
    content_type: str  # "slideshow", "narration", "video_transitions"
    topic: str
    title: str
    
    # Pipeline config
    image_model: str  # "gpt15", "flux", "dalle3", etc.
    font_name: str
    visual_style: str
    has_voice: bool
    has_video_transitions: bool
    
    # Output
    slides_count: int
    output_files: List[str] = field(default_factory=list)
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    
    # Cost
    estimated_cost: float = 0.0
    
    # Status
    status: str = "completed"  # "completed", "failed", "emailed"
    emailed: bool = False
    email_sent_at: Optional[str] = None
    
    # Extra metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductionHistory:
    """Manage production history."""
    
    def __init__(self):
        self.records: List[ProductionRecord] = []
        self._load()
    
    def _load(self):
        """Load history from disk."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.records = [ProductionRecord(**r) for r in data.get('records', [])]
            except Exception as e:
                print(f"Warning: Could not load history: {e}")
    
    def _save(self):
        """Save history to disk."""
        try:
            data = {
                'records': [asdict(r) for r in self.records],
                'last_updated': datetime.now().isoformat()
            }
            with open(HISTORY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_record(
        self,
        content_type: str,
        topic: str,
        title: str,
        image_model: str = "gpt15",
        font_name: str = "social",
        visual_style: str = "modern",
        has_voice: bool = False,
        has_video_transitions: bool = False,
        slides_count: int = 0,
        output_files: List[str] = None,
        video_path: str = None,
        audio_path: str = None,
        estimated_cost: float = 0.0,
        status: str = "completed",
        metadata: Dict[str, Any] = None
    ) -> ProductionRecord:
        """Add a new production record."""
        now = datetime.now()
        
        record = ProductionRecord(
            id=f"{content_type}_{now.strftime('%Y%m%d_%H%M%S')}",
            timestamp=now.isoformat(),
            date=now.strftime('%Y-%m-%d'),
            content_type=content_type,
            topic=topic,
            title=title,
            image_model=image_model,
            font_name=font_name,
            visual_style=visual_style,
            has_voice=has_voice,
            has_video_transitions=has_video_transitions,
            slides_count=slides_count,
            output_files=output_files or [],
            video_path=video_path,
            audio_path=audio_path,
            estimated_cost=estimated_cost,
            status=status,
            metadata=metadata or {}
        )
        
        self.records.append(record)
        self._save()
        return record
    
    def mark_emailed(self, record_id: str) -> bool:
        """Mark a record as emailed."""
        for record in self.records:
            if record.id == record_id:
                record.emailed = True
                record.email_sent_at = datetime.now().isoformat()
                record.status = "emailed"
                self._save()
                return True
        return False
    
    def get_all(self) -> List[ProductionRecord]:
        """Get all records, newest first."""
        return sorted(self.records, key=lambda r: r.timestamp, reverse=True)
    
    def get_by_date(self, date: str) -> List[ProductionRecord]:
        """Get records for a specific date (YYYY-MM-DD)."""
        return [r for r in self.records if r.date == date]
    
    def get_by_type(self, content_type: str) -> List[ProductionRecord]:
        """Get records by content type."""
        return [r for r in self.records if r.content_type == content_type]
    
    def get_today(self) -> List[ProductionRecord]:
        """Get today's records."""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_by_date(today)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get production statistics."""
        total = len(self.records)
        
        by_type = {}
        for r in self.records:
            if r.content_type not in by_type:
                by_type[r.content_type] = 0
            by_type[r.content_type] += 1
        
        by_model = {}
        for r in self.records:
            if r.image_model not in by_model:
                by_model[r.image_model] = 0
            by_model[r.image_model] += 1
        
        total_cost = sum(r.estimated_cost for r in self.records)
        total_slides = sum(r.slides_count for r in self.records)
        
        # Daily breakdown
        by_date = {}
        for r in self.records:
            if r.date not in by_date:
                by_date[r.date] = {'count': 0, 'cost': 0}
            by_date[r.date]['count'] += 1
            by_date[r.date]['cost'] += r.estimated_cost
        
        return {
            'total_productions': total,
            'by_type': by_type,
            'by_model': by_model,
            'total_cost': total_cost,
            'total_slides': total_slides,
            'by_date': by_date,
            'emailed_count': sum(1 for r in self.records if r.emailed)
        }
    
    def get_recent(self, limit: int = 20) -> List[ProductionRecord]:
        """Get most recent records."""
        return self.get_all()[:limit]


# Global instance
production_history = ProductionHistory()


# Convenience functions for use in other modules
def log_production(
    content_type: str,
    topic: str,
    title: str,
    **kwargs
) -> ProductionRecord:
    """Log a production to history."""
    return production_history.add_record(
        content_type=content_type,
        topic=topic,
        title=title,
        **kwargs
    )


def get_production_history() -> ProductionHistory:
    """Get the production history instance."""
    return production_history
