#!/usr/bin/env python3
"""
Automation Manager - Tracks and controls video generation automations.

This module provides:
- State persistence for active automations
- Start/pause/resume/stop controls
- Stats tracking (videos produced, model used, etc.)
"""

import os
import json
import time
import uuid
import subprocess
import signal
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


# File paths
AUTOMATIONS_STATE_FILE = "automations_state.json"
TOPICS_FILE = "topics.txt"
COMPLETED_FILE = "completed_topics.txt"
LOG_FILE = "automation.log"

# Separate topic files for different content types
NARRATION_TOPICS_FILE = "topics_narration.txt"  # Story-style topics that need voice
LIST_TOPICS_FILE = "topics_list.txt"  # List-style topics (5 philosophers, etc.) - no voice needed


class AutomationStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AutomationConfig:
    """Configuration for an automation instance."""
    id: str
    name: str
    description: str
    
    # Content type
    automation_type: str = "slideshow"  # "slideshow", "video_transitions", "slideshow_narration", "full_video"
    
    # Topic type - determines which topic file to use and whether voice is needed
    topic_type: str = "list"  # "list" (no voice) or "narration" (with voice)
    
    # Image generation
    image_model: str = "gpt15"  # "gpt15" (recommended), "flux", "nano", "dalle3"
    
    # Text overlay
    font_name: str = "social"  # "social", "montserrat", "cinzel", "cormorant", "bebas"
    visual_style: str = "modern"  # "modern", "elegant", "bold", "minimal"
    
    # Voice settings
    enable_voice: bool = False  # Whether to add voice narration
    
    # Video settings (only used for video types)
    transition: str = "crossfade"  # "crossfade", "fade_black", "slide_left", etc.
    transition_duration: float = 0.3
    enable_video_transitions: bool = False  # Whether to use AI video transitions
    
    # Scheduling
    schedule_mode: str = "loop"  # "loop", "smart", "single"
    topics: List[str] = None  # Topics to process (can be empty if using topics.txt)
    use_topic_file: str = "general"  # "general", "narration", "list" - which topic file to pull from
    recycle_topics: bool = False  # Whether to add completed topics back to queue
    
    # Metadata
    created_at: str = ""
    
    # Runtime state
    status: str = AutomationStatus.STOPPED
    pid: Optional[int] = None  # Process ID if running
    items_produced: int = 0  # Slides/videos produced
    current_topic: Optional[str] = None
    last_activity: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []


class AutomationManager:
    """Manages automation instances - start, pause, resume, stop, and track stats."""
    
    def __init__(self):
        self.automations: Dict[str, AutomationConfig] = {}
        self._load_state()
    
    def _load_state(self):
        """Load automations state from disk."""
        if os.path.exists(AUTOMATIONS_STATE_FILE):
            try:
                with open(AUTOMATIONS_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    for auto_id, auto_data in data.get('automations', {}).items():
                        self.automations[auto_id] = AutomationConfig(**auto_data)
            except Exception as e:
                print(f"Warning: Could not load automations state: {e}")
    
    def _save_state(self):
        """Persist automations state to disk."""
        try:
            data = {
                'automations': {
                    auto_id: asdict(auto_config) 
                    for auto_id, auto_config in self.automations.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            with open(AUTOMATIONS_STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving automations state: {e}")
    
    def _check_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is still running."""
        if pid is None:
            return False
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
            return True
        except (ProcessLookupError, PermissionError):
            return False
    
    def refresh_statuses(self):
        """Check all automations and update their statuses based on actual process state."""
        for auto_id, auto in self.automations.items():
            if auto.status == AutomationStatus.RUNNING:
                if auto.pid and not self._check_process_running(auto.pid):
                    # Process died unexpectedly
                    auto.status = AutomationStatus.STOPPED
                    auto.error_message = "Process terminated unexpectedly"
                    auto.last_activity = datetime.now().isoformat()
        self._save_state()
    
    def create_automation(
        self,
        name: str,
        description: str,
        automation_type: str = "slideshow",
        topic_type: str = "list",
        image_model: str = "gpt15",
        font_name: str = "social",
        visual_style: str = "modern",
        enable_voice: bool = False,
        transition: str = "crossfade",
        transition_duration: float = 0.3,
        enable_video_transitions: bool = False,
        schedule_mode: str = "loop",
        topics: List[str] = None,
        use_topic_file: str = "general",
        recycle_topics: bool = False
    ) -> AutomationConfig:
        """Create a new automation configuration.
        
        Args:
            name: Display name for the automation
            description: Description of what this automation does
            automation_type: Type of content to generate:
                - "slideshow": Images with text only
                - "video_transitions": Slideshow + AI video transitions
                - "slideshow_narration": Slideshow + voiceover
                - "full_video": Complete video with narration
            topic_type: Type of topics (determines voice needs):
                - "list": List-style (5 philosophers, etc.) - no voice needed
                - "narration": Story/narrative style - needs voice
            image_model: Which AI model for images:
                - "flux": Flux Schnell 1.1 (fast, recommended)
                - "gpt15": GPT Image 1.5 (detailed)
                - "nano": Gemini 3 Pro (expensive, paused)
                - "dalle3": DALL-E 3
            font_name: Font for text overlay:
                - "social": Clean sans-serif (default)
                - "montserrat", "cinzel", "cormorant", "bebas"
            visual_style: Visual styling ("modern", "elegant", "bold", "minimal")
            enable_voice: Whether to add voice narration
            transition: Video transition type (for video types)
            transition_duration: Transition duration in seconds
            enable_video_transitions: Whether to use AI video transitions
            schedule_mode: When to run ("loop", "smart", "single")
            topics: List of topics to process
            use_topic_file: Which topic file to use ("general", "narration", "list")
            recycle_topics: Whether to add completed topics back to queue
        """
        auto_id = str(uuid.uuid4())[:8]
        
        automation = AutomationConfig(
            id=auto_id,
            name=name,
            description=description,
            automation_type=automation_type,
            topic_type=topic_type,
            image_model=image_model,
            font_name=font_name,
            visual_style=visual_style,
            enable_voice=enable_voice,
            transition=transition,
            transition_duration=transition_duration,
            enable_video_transitions=enable_video_transitions,
            schedule_mode=schedule_mode,
            topics=topics or [],
            use_topic_file=use_topic_file,
            recycle_topics=recycle_topics,
            created_at=datetime.now().isoformat(),
            status=AutomationStatus.STOPPED
        )
        
        self.automations[auto_id] = automation
        self._save_state()
        return automation
    
    def start_automation(self, auto_id: str) -> bool:
        """Start an automation process."""
        if auto_id not in self.automations:
            return False
        
        auto = self.automations[auto_id]
        
        # If paused, we can resume
        if auto.status == AutomationStatus.PAUSED:
            auto.status = AutomationStatus.RUNNING
            auto.paused_at = None
            auto.last_activity = datetime.now().isoformat()
            self._save_state()
            return True
        
        # Determine which topic file to use
        topic_file = get_topic_file_path(auto.use_topic_file)
        
        # Build command based on automation type
        if auto.automation_type in ["slideshow", "video_transitions", "slideshow_narration"]:
            # Use slideshow_automation.py
            cmd = ["python", "slideshow_automation.py"]
            cmd.extend(["--model", auto.image_model])
            cmd.extend(["--type", auto.automation_type])
            cmd.extend(["--font", auto.font_name])
            cmd.extend(["--style", auto.visual_style])
            cmd.extend(["--auto-id", auto_id])
            cmd.extend(["--topics-file", topic_file])
            
            # Voice option
            if auto.enable_voice:
                cmd.append("--voice")
            
            # Video transitions option
            if auto.enable_video_transitions:
                cmd.append("--video-transitions")
            
            # Topic recycling
            if auto.recycle_topics:
                cmd.append("--recycle")
            
            if auto.schedule_mode == "loop":
                cmd.append("--loop")
        else:
            # Use auto_runner.py for full_video
            cmd = ["python", "auto_runner.py"]
            cmd.extend(["--image-model", auto.image_model])
            cmd.extend(["--transition", auto.transition])
            cmd.extend(["--transition-duration", str(auto.transition_duration)])
            
            if auto.schedule_mode == "loop":
                cmd.append("--loop")
            elif auto.schedule_mode == "smart":
                cmd.append("--smart")
        
        # If automation has specific topics, write them to the appropriate topic file
        if auto.topics:
            with open(topic_file, 'a') as f:
                for topic in auto.topics:
                    f.write(topic + "\n")
        
        try:
            # Start the process in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent
            )
            
            auto.pid = process.pid
            auto.status = AutomationStatus.RUNNING
            auto.started_at = datetime.now().isoformat()
            auto.last_activity = datetime.now().isoformat()
            auto.error_message = None
            
            self._save_state()
            return True
            
        except Exception as e:
            auto.status = AutomationStatus.ERROR
            auto.error_message = str(e)
            self._save_state()
            return False
    
    def pause_automation(self, auto_id: str) -> bool:
        """Pause an automation (sends SIGSTOP to process)."""
        if auto_id not in self.automations:
            return False
        
        auto = self.automations[auto_id]
        
        if auto.status != AutomationStatus.RUNNING or not auto.pid:
            return False
        
        try:
            os.kill(auto.pid, signal.SIGSTOP)
            auto.status = AutomationStatus.PAUSED
            auto.paused_at = datetime.now().isoformat()
            auto.last_activity = datetime.now().isoformat()
            self._save_state()
            return True
        except Exception as e:
            auto.error_message = f"Failed to pause: {e}"
            self._save_state()
            return False
    
    def resume_automation(self, auto_id: str) -> bool:
        """Resume a paused automation (sends SIGCONT to process)."""
        if auto_id not in self.automations:
            return False
        
        auto = self.automations[auto_id]
        
        if auto.status != AutomationStatus.PAUSED or not auto.pid:
            return False
        
        try:
            os.kill(auto.pid, signal.SIGCONT)
            auto.status = AutomationStatus.RUNNING
            auto.paused_at = None
            auto.last_activity = datetime.now().isoformat()
            self._save_state()
            return True
        except Exception as e:
            auto.error_message = f"Failed to resume: {e}"
            self._save_state()
            return False
    
    def stop_automation(self, auto_id: str) -> bool:
        """Stop an automation completely (kills process)."""
        if auto_id not in self.automations:
            return False
        
        auto = self.automations[auto_id]
        
        if auto.pid:
            try:
                # First try SIGTERM for graceful shutdown
                os.kill(auto.pid, signal.SIGTERM)
                time.sleep(1)
                
                # If still running, force kill
                if self._check_process_running(auto.pid):
                    os.kill(auto.pid, signal.SIGKILL)
            except Exception:
                pass  # Process might already be dead
        
        auto.status = AutomationStatus.STOPPED
        auto.pid = None
        auto.last_activity = datetime.now().isoformat()
        self._save_state()
        return True
    
    def delete_automation(self, auto_id: str) -> bool:
        """Delete an automation configuration (stops it first if running)."""
        if auto_id not in self.automations:
            return False
        
        self.stop_automation(auto_id)
        del self.automations[auto_id]
        self._save_state()
        return True
    
    def update_stats(self, auto_id: str, items_produced: int = None, current_topic: str = None):
        """Update automation statistics."""
        if auto_id not in self.automations:
            return
        
        auto = self.automations[auto_id]
        
        if items_produced is not None:
            auto.items_produced = items_produced
        if current_topic is not None:
            auto.current_topic = current_topic
        
        auto.last_activity = datetime.now().isoformat()
        self._save_state()
    
    def get_automation(self, auto_id: str) -> Optional[AutomationConfig]:
        """Get a specific automation."""
        return self.automations.get(auto_id)
    
    def get_all_automations(self) -> List[AutomationConfig]:
        """Get all automations."""
        self.refresh_statuses()
        return list(self.automations.values())
    
    def get_active_automations(self) -> List[AutomationConfig]:
        """Get only running or paused automations."""
        self.refresh_statuses()
        return [
            auto for auto in self.automations.values() 
            if auto.status in [AutomationStatus.RUNNING, AutomationStatus.PAUSED]
        ]
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all automations."""
        self.refresh_statuses()
        
        total = len(self.automations)
        running = sum(1 for a in self.automations.values() if a.status == AutomationStatus.RUNNING)
        paused = sum(1 for a in self.automations.values() if a.status == AutomationStatus.PAUSED)
        stopped = sum(1 for a in self.automations.values() if a.status == AutomationStatus.STOPPED)
        total_items = sum(a.items_produced for a in self.automations.values())
        
        # Count by automation type
        by_type = {}
        for auto in self.automations.values():
            atype = auto.automation_type
            if atype not in by_type:
                by_type[atype] = {"total": 0, "running": 0}
            by_type[atype]["total"] += 1
            if auto.status == AutomationStatus.RUNNING:
                by_type[atype]["running"] += 1
        
        # Count by image model
        by_model = {}
        for auto in self.automations.values():
            model = auto.image_model
            if model not in by_model:
                by_model[model] = {"total": 0, "running": 0}
            by_model[model]["total"] += 1
            if auto.status == AutomationStatus.RUNNING:
                by_model[model]["running"] += 1
        
        return {
            'total_automations': total,
            'running': running,
            'paused': paused,
            'stopped': stopped,
            'total_items_produced': total_items,
            'by_type': by_type,
            'by_model': by_model
        }


# Utility functions for integration with existing auto_runner.py

def get_pending_topics_count() -> int:
    """Get count of pending topics."""
    try:
        if os.path.exists(TOPICS_FILE):
            with open(TOPICS_FILE, 'r') as f:
                return sum(1 for line in f if line.strip())
    except Exception:
        pass
    return 0


def get_completed_topics_count() -> int:
    """Get count of completed topics."""
    try:
        if os.path.exists(COMPLETED_FILE):
            with open(COMPLETED_FILE, 'r') as f:
                return sum(1 for line in f if line.strip())
    except Exception:
        pass
    return 0


def get_recent_completed_topics(limit: int = 20) -> List[Dict[str, str]]:
    """Get recent completed topics with timestamps."""
    topics = []
    try:
        if os.path.exists(COMPLETED_FILE):
            with open(COMPLETED_FILE, 'r') as f:
                lines = f.readlines()
            
            for line in reversed(lines[-limit:]):
                line = line.strip()
                if ' - ' in line:
                    timestamp, topic = line.split(' - ', 1)
                    topics.append({
                        'timestamp': timestamp,
                        'topic': topic
                    })
    except Exception:
        pass
    return topics


def get_recent_logs(limit: int = 50) -> str:
    """Get recent automation logs."""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
            return "".join(lines[-limit:])
    except Exception:
        pass
    return ""


# =============================================================================
# AUTOMATION TYPES - Different content generation pipelines
# =============================================================================
AUTOMATION_TYPES = {
    "slideshow": {
        "name": "Slideshow Only",
        "description": "Generate image slides with text overlay (no voice/video)",
        "icon": "🎴",
        "has_voice": False,
        "has_video": False,
        "runner": "slideshow_automation.py"
    },
    "video_transitions": {
        "name": "Slideshow + Video Transitions",
        "description": "Slideshow with AI-generated video transitions between slides",
        "icon": "🎬",
        "has_voice": False,
        "has_video": True,
        "runner": "slideshow_automation.py"
    },
    "slideshow_narration": {
        "name": "Slideshow + Narration",
        "description": "Slideshow with ElevenLabs voiceover (no video)",
        "icon": "🎙️",
        "has_voice": True,
        "has_video": False,
        "runner": "slideshow_automation.py"
    },
    "full_video": {
        "name": "Full Video",
        "description": "Complete video with narration, images, and transitions",
        "icon": "🎥",
        "has_voice": True,
        "has_video": True,
        "runner": "auto_runner.py"
    }
}

# =============================================================================
# IMAGE MODELS - Available image generation backends
# =============================================================================
IMAGE_MODELS = {
    "flux": {
        "name": "Flux Schnell 1.1",
        "description": "Fast, good quality, great for moody aesthetics",
        "icon": "⚡",
        "provider": "fal.ai",
        "cost": "$"
    },
    "gpt15": {
        "name": "GPT Image 1.5",
        "description": "Detailed images, slightly slower, good for complex scenes",
        "icon": "🎨",
        "provider": "fal.ai",
        "cost": "$"
    },
    "nano": {
        "name": "Gemini 3 Pro Image",
        "description": "High quality but expensive (PAUSED by default)",
        "icon": "💎",
        "provider": "Google",
        "cost": "$$$",
        "paused": True
    },
    "dalle3": {
        "name": "DALL-E 3",
        "description": "Excellent prompt following, high quality",
        "icon": "🌟",
        "provider": "OpenAI",
        "cost": "$$"
    }
}

# =============================================================================
# FONT STYLES - Available text overlay fonts
# =============================================================================
FONT_STYLES = {
    "social": {
        "name": "Social Media (Clean)",
        "description": "Clean sans-serif, sentence case - perfect for TikTok/Instagram",
        "default": True
    },
    "montserrat": {
        "name": "Montserrat Bold",
        "description": "Modern geometric sans-serif"
    },
    "cinzel": {
        "name": "Cinzel (Classical)",
        "description": "Roman/classical capitals - ancient wisdom vibes"
    },
    "cormorant": {
        "name": "Cormorant Italic",
        "description": "Elegant italic - @philosophaire style"
    },
    "bebas": {
        "name": "Bebas Neue",
        "description": "Bold display font - very punchy"
    }
}

# =============================================================================
# TRANSITIONS - Video transition effects
# =============================================================================
TRANSITIONS = {
    "none": "No transition",
    "crossfade": "Smooth crossfade",
    "fade_black": "Fade through black",
    "slide_left": "Slide left",
    "slide_right": "Slide right",
    "slide_up": "Slide up"
}

# =============================================================================
# SCHEDULE MODES - When to run automations
# =============================================================================
SCHEDULE_MODES = {
    "loop": {
        "name": "Continuous Loop",
        "description": "Process topics continuously without schedule restrictions"
    },
    "smart": {
        "name": "Smart Schedule",
        "description": "Posts during optimal times: 8-10am, 1-3pm, 6-8pm PST"
    },
    "single": {
        "name": "Single Run",
        "description": "Process topics once and stop"
    }
}

# =============================================================================
# TOPIC TYPES - Different content styles that affect voice needs
# =============================================================================
TOPIC_TYPES = {
    "list": {
        "name": "List Style",
        "description": "5 philosophers, 7 quotes, etc. - Text slides only, no narration needed",
        "icon": "📋",
        "needs_voice": False,
        "example": "5 Philosophers Who Changed the World, 7 Stoic Quotes for Daily Life"
    },
    "narration": {
        "name": "Narrative Story",
        "description": "Story-driven content that benefits from voice narration",
        "icon": "🎙️",
        "needs_voice": True,
        "example": "The Death of Socrates, Marcus Aurelius and the Slave"
    }
}

# =============================================================================
# TOPIC FILE SOURCES - Where to pull topics from
# =============================================================================
TOPIC_FILES = {
    "general": {
        "name": "General Queue",
        "file": TOPICS_FILE,
        "description": "Main topic queue (topics.txt)"
    },
    "narration": {
        "name": "Narration Topics",
        "file": NARRATION_TOPICS_FILE,
        "description": "Story topics that need voice (topics_narration.txt)"
    },
    "list": {
        "name": "List Topics",
        "file": LIST_TOPICS_FILE,
        "description": "List-style topics, no voice (topics_list.txt)"
    }
}


# =============================================================================
# TOPIC MANAGEMENT FUNCTIONS
# =============================================================================

def get_topic_file_path(topic_source: str) -> str:
    """Get the file path for a topic source."""
    return TOPIC_FILES.get(topic_source, TOPIC_FILES["general"])["file"]


def get_topics_from_file(topic_source: str = "general") -> List[str]:
    """Get all topics from a specific topic file."""
    file_path = get_topic_file_path(topic_source)
    topics = []
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                topics = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return topics


def add_topic_to_file(topic: str, topic_source: str = "general") -> bool:
    """Add a topic to a specific topic file."""
    file_path = get_topic_file_path(topic_source)
    try:
        with open(file_path, 'a') as f:
            f.write(topic.strip() + "\n")
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        return False


def add_topics_to_file(topics: List[str], topic_source: str = "general") -> int:
    """Add multiple topics to a specific topic file. Returns count added."""
    file_path = get_topic_file_path(topic_source)
    added = 0
    try:
        with open(file_path, 'a') as f:
            for topic in topics:
                if topic.strip():
                    f.write(topic.strip() + "\n")
                    added += 1
        return added
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        return added


def get_topics_count_by_source(topic_source: str = "general") -> int:
    """Get count of topics in a specific file."""
    return len(get_topics_from_file(topic_source))


def recycle_topic(topic: str, topic_source: str = "general") -> bool:
    """
    Add a completed topic back to the queue for recycling.
    
    Args:
        topic: The topic to recycle
        topic_source: Which queue to add it back to
    
    Returns:
        True if successful
    """
    return add_topic_to_file(topic, topic_source)


def recycle_all_completed_topics(topic_source: str = "general", limit: int = None) -> int:
    """
    Move all completed topics back to a topic queue.
    
    Args:
        topic_source: Which queue to add topics to
        limit: Maximum number of topics to recycle (None = all)
    
    Returns:
        Count of topics recycled
    """
    recycled = 0
    try:
        if not os.path.exists(COMPLETED_FILE):
            return 0
        
        with open(COMPLETED_FILE, 'r') as f:
            lines = f.readlines()
        
        topics_to_recycle = []
        for line in lines:
            line = line.strip()
            if ' - ' in line:
                # Format: "2026-01-09 16:36:22 - Topic Name"
                topic = line.split(' - ', 1)[1].strip()
                topics_to_recycle.append(topic)
        
        if limit:
            topics_to_recycle = topics_to_recycle[:limit]
        
        recycled = add_topics_to_file(topics_to_recycle, topic_source)
        
    except Exception as e:
        print(f"Error recycling topics: {e}")
    
    return recycled


def clear_completed_topics() -> bool:
    """Clear the completed topics file."""
    try:
        with open(COMPLETED_FILE, 'w') as f:
            f.write("")
        return True
    except Exception as e:
        print(f"Error clearing completed topics: {e}")
        return False


def get_all_topic_stats() -> Dict[str, Any]:
    """Get statistics for all topic files."""
    stats = {}
    for source_key, source_info in TOPIC_FILES.items():
        file_path = source_info["file"]
        count = 0
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    count = sum(1 for line in f if line.strip())
        except Exception:
            pass
        
        stats[source_key] = {
            "name": source_info["name"],
            "file": file_path,
            "count": count,
            "exists": os.path.exists(file_path)
        }
    
    # Add completed count
    completed = 0
    try:
        if os.path.exists(COMPLETED_FILE):
            with open(COMPLETED_FILE, 'r') as f:
                completed = sum(1 for line in f if line.strip())
    except Exception:
        pass
    
    stats["completed"] = {
        "name": "Completed",
        "file": COMPLETED_FILE,
        "count": completed,
        "exists": os.path.exists(COMPLETED_FILE)
    }
    
    return stats
