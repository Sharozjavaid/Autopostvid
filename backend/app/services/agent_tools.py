"""
Agent Tools - Tool definitions and executor for Claude Opus 4.5 agent.

This module defines all the tools that Claude can call, wrapping the existing
API functionality into a format compatible with the Anthropic tool use API.

Each tool has:
- name: Unique identifier matching ^[a-zA-Z0-9_-]{1,64}$
- description: Detailed explanation of functionality, usage, and limitations
- input_schema: JSON Schema for expected parameters
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import services and models
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Project, Slide, Automation, AutomationRun
from ..services.prompt_config import CONTENT_TYPES, IMAGE_STYLES, list_content_types, list_image_styles


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOL_DEFINITIONS = [
    # -------------------------------------------------------------------------
    # SCRIPT GENERATION TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "generate_script",
        "description": """Generate a slideshow script from a topic. Creates a complete content structure for a TikTok slideshow including hook slide, content slides, and outro.

USE THIS WHEN: User wants to create new content about a topic.
RETURNS: Project ID, slides array with titles/subtitles/visuals, and total slide count.
NOTE: Script must be approved before generating images.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic for the slideshow, e.g., '5 philosophers who changed the world' or 'Marcus Aurelius on anger'"
                },
                "content_type": {
                    "type": "string",
                    "description": "Style of content generation. Options: wisdom_slideshow (default, 5-7 slides), mentor_slideshow (teaching style), stoic_lesson, philosophical_story",
                    "default": "wisdom_slideshow"
                },
                "image_style": {
                    "type": "string",
                    "description": "Visual style for images. Options: classical (oil paintings), cinematic (dramatic lighting), minimal (clean), golden_dust (particle effects)",
                    "default": "classical"
                }
            },
            "required": ["topic"]
        },
        "category": "script"
    },
    {
        "name": "approve_script",
        "description": """Approve a generated script to allow image generation to proceed.

USE THIS WHEN: User has reviewed the script and wants to generate images.
REQUIRED BEFORE: Generating any images for the project.
NOTE: Without approval, image generation will be blocked.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID from generate_script"
                }
            },
            "required": ["project_id"]
        },
        "category": "script"
    },
    {
        "name": "regenerate_slide_script",
        "description": """Regenerate the script for a specific slide with optional instructions.

USE THIS WHEN: User wants to change the text/content of a specific slide.
NOTE: This only changes the script, not the image. Image must be regenerated separately.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                },
                "slide_index": {
                    "type": "integer",
                    "description": "Which slide to regenerate (0-based index)"
                },
                "instruction": {
                    "type": "string",
                    "description": "Optional instruction for how to improve the slide, e.g., 'make it more dramatic' or 'focus on the stoic perspective'"
                }
            },
            "required": ["project_id", "slide_index"]
        },
        "category": "script"
    },
    {
        "name": "update_slide_content",
        "description": """Manually update a slide's text content (title, subtitle, visual description, narration).

USE THIS WHEN: User wants to directly edit specific text on a slide.
NOTE: Changes visual_description will require image regeneration.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                },
                "slide_id": {
                    "type": "string",
                    "description": "The slide ID to update"
                },
                "title": {
                    "type": "string",
                    "description": "New title text (optional)"
                },
                "subtitle": {
                    "type": "string",
                    "description": "New subtitle text (optional)"
                },
                "visual_description": {
                    "type": "string",
                    "description": "New visual description for image generation (optional)"
                },
                "narration": {
                    "type": "string",
                    "description": "New narration text for voiceover (optional)"
                }
            },
            "required": ["project_id", "slide_id"]
        },
        "category": "script"
    },

    # -------------------------------------------------------------------------
    # IMAGE GENERATION TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "generate_slide_image",
        "description": """Generate an image for a single slide. Creates AI background and applies text overlay.

USE THIS WHEN: User wants to generate or regenerate one specific slide's image.
REQUIRES: Script must be approved first.
NOTE: Uses the slide's visual_description to generate the background.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "slide_id": {
                    "type": "string",
                    "description": "The slide ID to generate image for"
                },
                "model": {
                    "type": "string",
                    "description": "Image generation model. Options: gpt15 (best quality), flux (fast), dalle3",
                    "default": "gpt15"
                },
                "font": {
                    "type": "string",
                    "description": "Font for text overlay. Options: social (default), tiktok, tiktok-bold, bebas, cinzel, cormorant, montserrat, oswald",
                    "default": "social"
                },
                "theme": {
                    "type": "string",
                    "description": "Visual theme. Options: golden_dust, oil_contrast, glitch_titans, scene_portrait",
                    "default": "golden_dust"
                }
            },
            "required": ["slide_id"]
        },
        "category": "images"
    },
    {
        "name": "generate_all_images",
        "description": """Generate images for all slides in a project (batch generation).

USE THIS WHEN: User wants to generate all slide images at once.
REQUIRES: Script must be approved first.
NOTE: This runs in the background and may take 1-2 minutes for 6 slides.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                },
                "model": {
                    "type": "string",
                    "description": "Image generation model: gpt15, flux, or dalle3",
                    "default": "gpt15"
                },
                "font": {
                    "type": "string",
                    "description": "Font for all slides: social, tiktok, bebas, cinzel, etc.",
                    "default": "social"
                },
                "theme": {
                    "type": "string",
                    "description": "Visual theme for all slides",
                    "default": "golden_dust"
                }
            },
            "required": ["project_id"]
        },
        "category": "images"
    },
    {
        "name": "change_slide_font",
        "description": """Re-apply text overlay with a different font. FAST - reuses existing background image.

USE THIS WHEN: User wants to try a different font on an existing slide.
NOTE: This is much faster than regenerating the full image since it only re-renders text.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "slide_id": {
                    "type": "string",
                    "description": "The slide ID"
                },
                "font": {
                    "type": "string",
                    "description": "New font to apply. Options: social, tiktok, tiktok-bold, bebas, cinzel, cormorant, montserrat, oswald"
                }
            },
            "required": ["slide_id", "font"]
        },
        "category": "images"
    },
    {
        "name": "get_slide_versions",
        "description": """Get version history for a slide showing all past changes.

USE THIS WHEN: User wants to see previous versions or undo a change.
RETURNS: List of versions with timestamps, fonts, themes used.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "slide_id": {
                    "type": "string",
                    "description": "The slide ID"
                }
            },
            "required": ["slide_id"]
        },
        "category": "images"
    },
    {
        "name": "revert_slide_version",
        "description": """Revert a slide to a previous version.

USE THIS WHEN: User wants to undo changes and go back to an earlier version.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "slide_id": {
                    "type": "string",
                    "description": "The slide ID"
                },
                "version_number": {
                    "type": "integer",
                    "description": "The version number to revert to"
                }
            },
            "required": ["slide_id", "version_number"]
        },
        "category": "images"
    },

    # -------------------------------------------------------------------------
    # PROJECT MANAGEMENT TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "list_projects",
        "description": """List all projects with optional filtering.

USE THIS WHEN: User wants to see their existing projects or find a specific one.
RETURNS: Array of projects with IDs, names, status, and slide counts.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: script_review, script_approved, generating, complete"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of projects to return",
                    "default": 20
                }
            }
        },
        "category": "projects"
    },
    {
        "name": "get_project",
        "description": """Get detailed information about a specific project including all slides.

USE THIS WHEN: User wants to see the current state of a project.
RETURNS: Project details with all slides, their content, and image statuses.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                }
            },
            "required": ["project_id"]
        },
        "category": "projects"
    },
    {
        "name": "delete_project",
        "description": """Delete a project and all its slides.

USE THIS WHEN: User wants to remove a project permanently.
WARNING: This cannot be undone.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to delete"
                }
            },
            "required": ["project_id"]
        },
        "category": "projects"
    },
    {
        "name": "get_project_stats",
        "description": """Get statistics for a project: completed slides, pending, errors.

USE THIS WHEN: User wants a quick status update on generation progress.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                }
            },
            "required": ["project_id"]
        },
        "category": "projects"
    },

    # -------------------------------------------------------------------------
    # TIKTOK INTEGRATION TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "check_tiktok_status",
        "description": """Check if TikTok is connected and authenticated.

USE THIS WHEN: Before attempting to upload to TikTok.
RETURNS: Connection status, authenticated user info if connected.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "tiktok"
    },
    {
        "name": "get_tiktok_auth_url",
        "description": """Get the TikTok OAuth URL for connecting an account.

USE THIS WHEN: User wants to connect their TikTok account.
RETURNS: URL to redirect user for TikTok authorization.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "tiktok"
    },
    {
        "name": "upload_to_tiktok",
        "description": """Upload a video to TikTok (to drafts by default).

USE THIS WHEN: User wants to post content to TikTok.
REQUIRES: TikTok must be connected first. Video file must exist.
NOTE: Uploads to drafts for user review before publishing.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "title": {
                    "type": "string",
                    "description": "Caption/title for the TikTok post"
                },
                "to_inbox": {
                    "type": "boolean",
                    "description": "If true, upload to drafts (safer). If false, publish directly.",
                    "default": True
                }
            },
            "required": ["video_path", "title"]
        },
        "category": "tiktok"
    },
    {
        "name": "get_upload_status",
        "description": """Check the status of a TikTok upload.

USE THIS WHEN: After uploading, to confirm it succeeded.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "publish_id": {
                    "type": "string",
                    "description": "The publish ID from upload_to_tiktok"
                }
            },
            "required": ["publish_id"]
        },
        "category": "tiktok"
    },
    {
        "name": "post_slideshow_to_tiktok",
        "description": """Post a photo slideshow to TikTok drafts (user's inbox).

USE THIS WHEN: User wants to send generated slides to their TikTok drafts as a photo carousel/slideshow.
REQUIRES: 
- TikTok must be connected first
- Project must have completed images (at least 2 slides with final_image_path)

HOW IT WORKS:
1. Takes a project_id and gets all slides with completed images
2. Uses TikTok's photo posting API to send images to user's drafts
3. User can then edit and publish from their TikTok app

NOTE: This creates a PHOTO carousel, not a video. Images appear as swipeable slides in TikTok.
IMPORTANT: Images must be JPEG format - the system automatically handles this conversion.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID containing the slides to post"
                },
                "caption": {
                    "type": "string",
                    "description": "Caption/title for the TikTok post (optional, defaults to project topic)"
                }
            },
            "required": ["project_id"]
        },
        "category": "tiktok"
    },

    # -------------------------------------------------------------------------
    # INSTAGRAM TOOLS (via Post Bridge API)
    # -------------------------------------------------------------------------
    {
        "name": "check_instagram_status",
        "description": """Check if Instagram is connected via Post Bridge API.

USE THIS WHEN: User asks about Instagram connection or before posting to Instagram.
RETURNS: Connection status and account info if connected.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "instagram"
    },
    {
        "name": "post_slideshow_to_instagram",
        "description": """Post a photo carousel/slideshow to Instagram.

USE THIS WHEN: User wants to post generated slides to Instagram as a carousel/slideshow.
REQUIRES: 
- Instagram connected via Post Bridge (check with check_instagram_status first)
- Project must have completed images (at least 2 slides with final_image_path)

HOW IT WORKS:
1. Takes a project_id and gets all slides with completed images
2. Uploads images to Post Bridge
3. Creates a carousel post on Instagram
4. Returns the Instagram post URL when complete

NOTE: This posts directly to Instagram (not drafts). Images appear as swipeable carousel.
HASHTAGS: Optional array of hashtags (without #) - e.g., ["philosophy", "wisdom", "stoicism"]""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID containing the slides to post"
                },
                "caption": {
                    "type": "string",
                    "description": "Caption for the Instagram post (optional, defaults to project topic)"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hashtags to add (without #). E.g., ['philosophy', 'wisdom']"
                }
            },
            "required": ["project_id"]
        },
        "category": "instagram"
    },
    {
        "name": "get_instagram_post_status",
        "description": """Check the status of an Instagram post.

USE THIS WHEN: User wants to check if their Instagram post succeeded.
RETURNS: Post status and URL if published.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "The post ID from post_slideshow_to_instagram"
                }
            },
            "required": ["post_id"]
        },
        "category": "instagram"
    },

    # -------------------------------------------------------------------------
    # AUTOMATION TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "list_automations",
        "description": """List all automation recipes.

USE THIS WHEN: User wants to see their scheduled automations.
RETURNS: Array of automations with status, schedule, and run counts.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: running, stopped, paused"
                }
            }
        },
        "category": "automations"
    },
    {
        "name": "create_automation",
        "description": """Create a new automation recipe for scheduled content generation.

USE THIS WHEN: User wants to set up automatic daily/weekly content creation.
NOTE: Automation starts in 'stopped' state - must be started separately.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the automation"
                },
                "content_type": {
                    "type": "string",
                    "description": "Content style: wisdom_slideshow, mentor_slideshow, etc.",
                    "default": "wisdom_slideshow"
                },
                "image_style": {
                    "type": "string",
                    "description": "Image style: classical, cinematic, minimal, etc.",
                    "default": "classical"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Queue of topics to cycle through"
                },
                "schedule_times": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Times to run, e.g., ['09:00', '18:00']"
                },
                "schedule_days": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Days to run, e.g., ['monday', 'wednesday', 'friday']"
                }
            },
            "required": ["name"]
        },
        "category": "automations"
    },
    {
        "name": "start_automation",
        "description": """Start an automation - schedules it to run at configured times.

USE THIS WHEN: User wants to activate an automation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "The automation ID"
                }
            },
            "required": ["automation_id"]
        },
        "category": "automations"
    },
    {
        "name": "stop_automation",
        "description": """Stop an automation - removes it from the scheduler.

USE THIS WHEN: User wants to deactivate an automation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "The automation ID"
                }
            },
            "required": ["automation_id"]
        },
        "category": "automations"
    },
    {
        "name": "run_automation_now",
        "description": """Trigger an immediate run of an automation for testing.

USE THIS WHEN: User wants to test an automation without waiting for schedule.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "The automation ID"
                }
            },
            "required": ["automation_id"]
        },
        "category": "automations"
    },
    {
        "name": "add_topics_to_automation",
        "description": """Add topics to an automation's queue.

USE THIS WHEN: User wants to add more topics to an existing automation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "The automation ID"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topics to add to the queue"
                }
            },
            "required": ["automation_id", "topics"]
        },
        "category": "automations"
    },
    {
        "name": "get_automation_runs",
        "description": """Get run history for an automation.

USE THIS WHEN: User wants to see past runs and their success/failure status.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "The automation ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum runs to return",
                    "default": 20
                }
            },
            "required": ["automation_id"]
        },
        "category": "automations"
    },

    # -------------------------------------------------------------------------
    # SETTINGS & INFO TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "list_fonts",
        "description": """Get all available fonts for text overlay.

USE THIS WHEN: User asks about font options.
RETURNS: Array of fonts with IDs, names, and style descriptions.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "settings"
    },
    {
        "name": "list_content_types",
        "description": """Get all available content types for script generation.

USE THIS WHEN: User asks about content style options.
RETURNS: Array of content types with descriptions and slide counts.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "settings"
    },
    {
        "name": "list_image_styles",
        "description": """Get all available image styles for generation.

USE THIS WHEN: User asks about visual style options.
RETURNS: Array of image styles with descriptions.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "settings"
    },
    {
        "name": "list_themes",
        "description": """Get all available themes (legacy system).

USE THIS WHEN: User asks about theme options.
RETURNS: Array of themes with IDs and names.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "settings"
    },
    {
        "name": "get_health_status",
        "description": """Check the health of all connected services (Gemini, ElevenLabs, OpenAI, fal.ai).

USE THIS WHEN: User wants to verify all services are working.
RETURNS: Status of each service connection.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "settings"
    },

    # -------------------------------------------------------------------------
    # MEMORY & SESSION TOOLS
    # -------------------------------------------------------------------------
    {
        "name": "get_session_context",
        "description": """Load saved session context including active project and conversation summary.

USE THIS WHEN: At the START of a new conversation to see what you were working on.
RETURNS: Active project ID, conversation summary, and any saved insights.
NOTE: Always call this first in a new session to maintain continuity.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        },
        "category": "memory"
    },
    {
        "name": "save_session_context",
        "description": """Save the current session context for continuity across restarts.

USE THIS WHEN: 
- After creating or selecting a project
- Before the conversation might end
- When user says goodbye or pauses
- After completing significant work

WHAT TO SAVE:
- project_id: The current project you're working on
- summary: Brief summary of what happened this session (1-3 sentences)

This ensures you remember what you were doing if the session is interrupted.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The active project ID (optional - set to null to clear)"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of the current session (what was done, what's pending)"
                }
            },
            "required": ["summary"]
        },
        "category": "memory"
    },
    {
        "name": "add_agent_insight",
        "description": """Add a learning or insight to your persistent memory.

USE THIS WHEN:
- You learn a user preference (e.g., "User prefers TikTok Bold font")
- You discover something that works well (e.g., "Oil contrast theme works great for dark topics")
- You notice a pattern worth remembering

CATEGORIES:
- 'User Preferences': Things the user likes/dislikes
- 'Learnings': What you've learned about creating good content
- 'Style Notes': Specific style preferences
- 'Topics': Topics that performed well or should be avoided

These insights persist across sessions and help you improve over time.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category: 'User Preferences', 'Learnings', 'Style Notes', or 'Topics'"
                },
                "insight": {
                    "type": "string",
                    "description": "The insight to remember"
                }
            },
            "required": ["category", "insight"]
        },
        "category": "memory"
    },
]


# =============================================================================
# TOOL EXECUTOR
# =============================================================================

class ToolExecutor:
    """
    Executes tools called by Claude and returns results.
    
    Each tool method corresponds to a tool definition above and wraps
    the existing API functionality.
    """
    
    def __init__(self):
        """Initialize the tool executor."""
        pass
    
    def get_db(self) -> Session:
        """Get a database session."""
        return SessionLocal()
    
    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool parameters
        
        Returns:
            Result dictionary with success status and data or error
        """
        # Map tool names to methods
        tool_methods = {
            # Script tools
            "generate_script": self._generate_script,
            "approve_script": self._approve_script,
            "regenerate_slide_script": self._regenerate_slide_script,
            "update_slide_content": self._update_slide_content,
            # Image tools
            "generate_slide_image": self._generate_slide_image,
            "generate_all_images": self._generate_all_images,
            "change_slide_font": self._change_slide_font,
            "get_slide_versions": self._get_slide_versions,
            "revert_slide_version": self._revert_slide_version,
            # Project tools
            "list_projects": self._list_projects,
            "get_project": self._get_project,
            "delete_project": self._delete_project,
            "get_project_stats": self._get_project_stats,
            # TikTok tools
            "check_tiktok_status": self._check_tiktok_status,
            "get_tiktok_auth_url": self._get_tiktok_auth_url,
            "upload_to_tiktok": self._upload_to_tiktok,
            "get_upload_status": self._get_upload_status,
            "post_slideshow_to_tiktok": self._post_slideshow_to_tiktok,
            # Instagram tools
            "check_instagram_status": self._check_instagram_status,
            "post_slideshow_to_instagram": self._post_slideshow_to_instagram,
            "get_instagram_post_status": self._get_instagram_post_status,
            # Automation tools
            "list_automations": self._list_automations,
            "create_automation": self._create_automation,
            "start_automation": self._start_automation,
            "stop_automation": self._stop_automation,
            "run_automation_now": self._run_automation_now,
            "add_topics_to_automation": self._add_topics_to_automation,
            "get_automation_runs": self._get_automation_runs,
            # Settings tools
            "list_fonts": self._list_fonts,
            "list_content_types": self._list_content_types,
            "list_image_styles": self._list_image_styles,
            "list_themes": self._list_themes,
            "get_health_status": self._get_health_status,
            # Memory tools
            "get_session_context": self._get_session_context,
            "save_session_context": self._save_session_context,
            "add_agent_insight": self._add_agent_insight,
        }
        
        if tool_name not in tool_methods:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            method = tool_methods[tool_name]
            result = await method(**tool_input)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # -------------------------------------------------------------------------
    # SCRIPT TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _generate_script(
        self,
        topic: str,
        content_type: str = "wisdom_slideshow",
        image_style: str = "classical"
    ) -> Dict[str, Any]:
        """Generate a script for a topic."""
        from .gemini_handler import GeminiHandler
        
        db = self.get_db()
        try:
            handler = GeminiHandler()
            
            # Validate content type
            if content_type not in CONTENT_TYPES:
                content_type = "wisdom_slideshow"
            
            # Generate script
            if content_type in CONTENT_TYPES:
                enhanced_topic = handler.enhance_topic_prompt(topic)
                result = handler.generate_script(enhanced_topic, content_type)
            else:
                result = handler._generate_narrative_story(topic, num_scenes=7)
            
            if not result:
                return {"success": False, "error": "Script generation failed"}
            
            # Create project
            project = Project(
                name=topic[:100],
                topic=topic,
                content_type="slideshow",
                script_style=content_type,
                status="script_review",
                script_approved="N",
                settings={"image_style": image_style}
            )
            db.add(project)
            db.flush()
            
            # Create slides
            scenes = result.get("scenes", result.get("slides", []))
            slides_data = []
            
            for i, scene in enumerate(scenes):
                title = scene.get("title", scene.get("hook", scene.get("display_text", "")))
                subtitle = scene.get("subtitle", scene.get("text", scene.get("content", "")))
                visual = scene.get("visual_description", scene.get("visual", ""))
                narration = scene.get("narration", scene.get("script", ""))
                
                slide = Slide(
                    project_id=project.id,
                    order_index=i,
                    title=title,
                    subtitle=subtitle,
                    visual_description=visual,
                    narration=narration
                )
                db.add(slide)
                slides_data.append({
                    "index": i,
                    "title": title,
                    "subtitle": subtitle,
                    "visual_description": visual
                })
            
            db.commit()
            
            return {
                "success": True,
                "project_id": project.id,
                "topic": topic,
                "content_type": content_type,
                "image_style": image_style,
                "total_slides": len(slides_data),
                "slides": slides_data,
                "status": "script_review",
                "message": "Script generated. Review the slides and call approve_script to proceed with image generation."
            }
        finally:
            db.close()
    
    async def _approve_script(self, project_id: str) -> Dict[str, Any]:
        """Approve a script for image generation."""
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            project.script_approved = "Y"
            project.status = "script_approved"
            db.commit()
            
            return {
                "success": True,
                "project_id": project_id,
                "status": "script_approved",
                "message": "Script approved. You can now generate images."
            }
        finally:
            db.close()
    
    async def _regenerate_slide_script(
        self,
        project_id: str,
        slide_index: int,
        instruction: str = None
    ) -> Dict[str, Any]:
        """Regenerate script for a specific slide."""
        from .gemini_handler import GeminiHandler
        
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            slide = db.query(Slide).filter(
                Slide.project_id == project_id,
                Slide.order_index == slide_index
            ).first()
            
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            handler = GeminiHandler()
            
            prompt = f"""
            Regenerate this slide for the topic: {project.topic}
            
            Current content:
            - Title: {slide.title}
            - Subtitle: {slide.subtitle}
            - Visual: {slide.visual_description}
            
            {f"Special instruction: {instruction}" if instruction else "Make it more engaging and impactful."}
            
            Return JSON with: title, subtitle, visual_description
            """
            
            response = handler.client.models.generate_content(
                model=handler.text_model_name,
                contents=prompt
            )
            
            result = json.loads(handler._clean_json_text(response.text))
            
            slide.title = result.get("title", slide.title)
            slide.subtitle = result.get("subtitle", slide.subtitle)
            slide.visual_description = result.get("visual_description", slide.visual_description)
            slide.image_status = "pending"
            
            db.commit()
            
            return {
                "success": True,
                "slide_index": slide_index,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "visual_description": slide.visual_description,
                "message": "Slide script regenerated. Image needs to be regenerated."
            }
        finally:
            db.close()
    
    async def _update_slide_content(
        self,
        project_id: str,
        slide_id: str,
        title: str = None,
        subtitle: str = None,
        visual_description: str = None,
        narration: str = None
    ) -> Dict[str, Any]:
        """Update slide content manually."""
        db = self.get_db()
        try:
            slide = db.query(Slide).filter(
                Slide.id == slide_id,
                Slide.project_id == project_id
            ).first()
            
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            if title is not None:
                slide.title = title
            if subtitle is not None:
                slide.subtitle = subtitle
            if visual_description is not None:
                slide.visual_description = visual_description
                slide.image_status = "pending"
            if narration is not None:
                slide.narration = narration
            
            db.commit()
            
            return {
                "success": True,
                "slide_id": slide_id,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "message": "Slide content updated."
            }
        finally:
            db.close()
    
    # -------------------------------------------------------------------------
    # IMAGE TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _generate_slide_image(
        self,
        slide_id: str,
        model: str = "gpt15",
        font: str = "social",
        theme: str = "golden_dust"
    ) -> Dict[str, Any]:
        """Generate image for a single slide."""
        # Import here to avoid circular imports
        from ..routers.images import generate_single_image
        
        db = self.get_db()
        try:
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            # Check if script is approved
            project = db.query(Project).filter(Project.id == slide.project_id).first()
            if project and project.script_approved != "Y":
                return {"success": False, "error": "Script must be approved before generating images. Call approve_script first."}
            
            result = await generate_single_image(
                slide=slide,
                model=model,
                font=font,
                db=db,
                project_id=slide.project_id,
                theme_id=theme
            )
            
            # Refresh slide to get updated paths
            db.refresh(slide)
            
            # Build rich structured response for frontend
            if result.status == "success":
                return {
                    "success": True,
                    "slide_id": slide_id,
                    "slide_index": slide.order_index,
                    "project_id": slide.project_id,
                    "content": {
                        "title": slide.title,
                        "subtitle": slide.subtitle,
                    },
                    "image": {
                        "url": result.final_image_url,
                        "background_url": result.background_image_url,
                        "width": 1080,
                        "height": 1920,
                    },
                    "settings": {
                        "font": font,
                        "theme": theme,
                        "model": model,
                    },
                    "type": "slide_preview"  # Marker for frontend
                }
            else:
                return {
                    "success": False,
                    "slide_id": slide_id,
                    "error": result.error_message
                }
        finally:
            db.close()
    
    async def _generate_all_images(
        self,
        project_id: str,
        model: str = "gpt15",
        font: str = "social",
        theme: str = "golden_dust"
    ) -> Dict[str, Any]:
        """Generate images for all slides in a project."""
        from ..routers.images import generate_single_image
        
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            if project.script_approved != "Y":
                return {"success": False, "error": "Script must be approved before generating images."}
            
            slides = db.query(Slide).filter(
                Slide.project_id == project_id
            ).order_by(Slide.order_index).all()
            
            results = []
            slide_previews = []
            
            for slide in slides:
                result = await generate_single_image(
                    slide=slide,
                    model=model,
                    font=font,
                    db=db,
                    project_id=project_id,
                    theme_id=theme
                )
                
                # Refresh to get updated paths
                db.refresh(slide)
                
                slide_result = {
                    "slide_index": slide.order_index,
                    "slide_id": slide.id,
                    "success": result.status == "success",
                    "final_image_url": result.final_image_url
                }
                results.append(slide_result)
                
                # Build rich preview data for successful generations
                if result.status == "success":
                    slide_previews.append({
                        "slide_id": slide.id,
                        "slide_index": slide.order_index,
                        "project_id": project_id,
                        "content": {
                            "title": slide.title,
                            "subtitle": slide.subtitle,
                        },
                        "image": {
                            "url": result.final_image_url,
                            "background_url": result.background_image_url,
                            "width": 1080,
                            "height": 1920,
                        },
                        "settings": {
                            "font": font,
                            "theme": theme,
                            "model": model,
                        },
                        "type": "slide_preview"
                    })
            
            project.status = "complete"
            db.commit()
            
            successful = sum(1 for r in results if r["success"])
            
            return {
                "success": successful == len(results),
                "project_id": project_id,
                "total_slides": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "slides": results,
                "slide_previews": slide_previews,  # Rich preview data for frontend
                "type": "batch_slide_preview"  # Marker for frontend
            }
        finally:
            db.close()
    
    async def _change_slide_font(self, slide_id: str, font: str) -> Dict[str, Any]:
        """Re-apply text with a different font."""
        from ..routers.images import get_text_overlay
        from ..config import get_settings
        
        settings = get_settings()
        db = self.get_db()
        try:
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            if not slide.background_image_path and not slide.final_image_path:
                return {"success": False, "error": "No image exists. Generate an image first."}
            
            background_path = slide.background_image_path or slide.final_image_path
            
            project = db.query(Project).filter(Project.id == slide.project_id).first()
            total_slides = len(project.slides) if project else 1
            
            is_hook = slide.order_index == 0
            is_outro = slide.order_index == total_slides - 1
            
            overlay = get_text_overlay()
            final_path = str(settings.generated_slides_dir / f"{slide.id}_final.png")
            
            if is_hook:
                overlay.create_hook_slide(
                    background_path=background_path,
                    output_path=final_path,
                    hook_text=slide.subtitle or slide.title or "Philosophy",
                    font_name=font,
                    style="modern"
                )
            elif is_outro:
                overlay.create_outro_slide(
                    background_path=background_path,
                    output_path=final_path,
                    text=slide.title or "YOUR CHOICE",
                    subtitle=slide.subtitle,
                    font_name=font
                )
            else:
                overlay.create_slide(
                    background_path=background_path,
                    output_path=final_path,
                    title=slide.title or "",
                    subtitle=slide.subtitle or "",
                    slide_number=slide.order_index,
                    font_name=font,
                    style="modern"
                )
            
            old_font = slide.current_font or "unknown"
            version = slide.create_version(
                db=db,
                change_type="font_change",
                change_description=f"Changed font from {old_font} to {font}",
                font=font,
                theme=slide.current_theme
            )
            
            slide.final_image_path = final_path
            slide.current_font = font
            slide.image_status = "complete"
            db.commit()
            
            return {
                "success": True,
                "slide_id": slide_id,
                "font": font,
                "final_image_url": f"/static/slides/{Path(final_path).name}",
                "version": version.version_number,
                "message": f"Font changed to {font}"
            }
        finally:
            db.close()
    
    async def _get_slide_versions(self, slide_id: str) -> Dict[str, Any]:
        """Get version history for a slide."""
        from ..models import SlideVersion
        
        db = self.get_db()
        try:
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            versions = db.query(SlideVersion).filter(
                SlideVersion.slide_id == slide_id
            ).order_by(SlideVersion.version_number.desc()).all()
            
            return {
                "success": True,
                "slide_id": slide_id,
                "current_version": slide.current_version,
                "total_versions": len(versions),
                "versions": [v.to_dict() for v in versions]
            }
        finally:
            db.close()
    
    async def _revert_slide_version(self, slide_id: str, version_number: int) -> Dict[str, Any]:
        """Revert slide to a previous version."""
        from ..models import SlideVersion
        
        db = self.get_db()
        try:
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if not slide:
                return {"success": False, "error": "Slide not found"}
            
            version = db.query(SlideVersion).filter(
                SlideVersion.slide_id == slide_id,
                SlideVersion.version_number == version_number
            ).first()
            
            if not version:
                return {"success": False, "error": f"Version {version_number} not found"}
            
            if not version.final_image_path or not os.path.exists(version.final_image_path):
                return {"success": False, "error": "Version image file no longer exists"}
            
            # Create revert version
            revert_version = slide.create_version(
                db=db,
                change_type="revert",
                change_description=f"Reverted to version {version_number}",
                font=version.font,
                theme=version.theme
            )
            
            # Restore content
            slide.title = version.title
            slide.subtitle = version.subtitle
            slide.visual_description = version.visual_description
            slide.narration = version.narration
            slide.current_font = version.font
            slide.current_theme = version.theme
            slide.final_image_path = version.final_image_path
            slide.background_image_path = version.background_image_path
            slide.image_status = "complete"
            db.commit()
            
            return {
                "success": True,
                "slide_id": slide_id,
                "reverted_to": version_number,
                "new_version": revert_version.version_number
            }
        finally:
            db.close()
    
    # -------------------------------------------------------------------------
    # PROJECT TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _list_projects(
        self,
        status: str = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List all projects."""
        db = self.get_db()
        try:
            query = db.query(Project)
            if status:
                query = query.filter(Project.status == status)
            
            projects = query.order_by(Project.updated_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "topic": p.topic,
                        "status": p.status,
                        "slide_count": len(p.slides),
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    }
                    for p in projects
                ],
                "total": len(projects)
            }
        finally:
            db.close()
    
    async def _get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            slides = sorted(project.slides, key=lambda s: s.order_index)
            
            return {
                "success": True,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "topic": project.topic,
                    "status": project.status,
                    "script_approved": project.script_approved == "Y",
                    "settings": project.settings,
                    "slides": [
                        {
                            "id": s.id,
                            "index": s.order_index,
                            "title": s.title,
                            "subtitle": s.subtitle,
                            "visual_description": s.visual_description,
                            "image_status": s.image_status,
                            "current_font": s.current_font,
                            "final_image_url": f"/static/slides/{Path(s.final_image_path).name}" if s.final_image_path else None
                        }
                        for s in slides
                    ]
                }
            }
        finally:
            db.close()
    
    async def _delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project."""
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            db.delete(project)
            db.commit()
            
            return {
                "success": True,
                "message": f"Project '{project.name}' deleted"
            }
        finally:
            db.close()
    
    async def _get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get project statistics."""
        db = self.get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            total = len(project.slides)
            completed = sum(1 for s in project.slides if s.image_status == "complete")
            pending = sum(1 for s in project.slides if s.image_status == "pending")
            errors = sum(1 for s in project.slides if s.image_status == "error")
            
            return {
                "success": True,
                "project_id": project_id,
                "total_slides": total,
                "completed": completed,
                "pending": pending,
                "errors": errors,
                "progress_percent": round((completed / total * 100) if total > 0 else 0, 1)
            }
        finally:
            db.close()
    
    # -------------------------------------------------------------------------
    # TIKTOK TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _check_tiktok_status(self) -> Dict[str, Any]:
        """Check TikTok connection status."""
        from ..routers.tiktok import get_tiktok_config, load_tokens
        
        config = get_tiktok_config()
        tokens = load_tokens()
        
        return {
            "success": True,
            "configured": bool(config["client_key"] and config["client_secret"]),
            "authenticated": bool(tokens and tokens.get("access_token")),
            "open_id": tokens.get("open_id") if tokens else None,
            "scope": tokens.get("scope") if tokens else None
        }
    
    async def _get_tiktok_auth_url(self) -> Dict[str, Any]:
        """Get TikTok OAuth URL."""
        from ..routers.tiktok import get_tiktok_config, generate_pkce_pair, save_pkce
        import secrets
        
        config = get_tiktok_config()
        
        if not config["client_key"]:
            return {"success": False, "error": "TikTok client key not configured"}
        
        code_verifier, code_challenge = generate_pkce_pair()
        save_pkce(code_verifier)
        
        csrf_state = secrets.token_urlsafe(16)
        redirect_uri = config["redirect_uri"] or "https://api.cofndrly.com/api/tiktok/callback"
        
        AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
        
        params = {
            "client_key": config["client_key"],
            "scope": "user.info.basic,video.upload,video.publish",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": csrf_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{AUTH_URL}?{param_str}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "redirect_uri": redirect_uri
        }
    
    async def _upload_to_tiktok(
        self,
        video_path: str,
        title: str,
        to_inbox: bool = True
    ) -> Dict[str, Any]:
        """Upload video to TikTok."""
        from ..routers.tiktok import load_tokens
        import requests
        
        tokens = load_tokens()
        
        if not tokens or not tokens.get("access_token"):
            return {"success": False, "error": "Not authenticated. Connect TikTok first."}
        
        video_file = Path(video_path)
        if not video_file.exists():
            return {"success": False, "error": f"Video file not found: {video_path}"}
        
        file_size = video_file.stat().st_size
        access_token = tokens["access_token"]
        
        init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/" if to_inbox else "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
        if to_inbox:
            init_data = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1
                }
            }
        else:
            init_data = {
                "post_info": {
                    "title": title,
                    "privacy_level": "SELF_ONLY",
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1
                }
            }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        init_response = requests.post(init_url, headers=headers, json=init_data)
        
        if init_response.status_code != 200:
            return {"success": False, "error": f"Init failed: {init_response.text}"}
        
        init_result = init_response.json()
        data = init_result.get("data", {})
        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")
        
        if not upload_url:
            return {"success": False, "error": "No upload URL in response"}
        
        with open(video_file, 'rb') as f:
            video_data = f.read()
        
        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
        }
        
        upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
        
        if upload_response.status_code not in [200, 201, 202]:
            return {"success": False, "error": f"Upload failed: {upload_response.text}"}
        
        return {
            "success": True,
            "publish_id": publish_id,
            "destination": "inbox" if to_inbox else "publish",
            "message": "Video uploaded to TikTok drafts!" if to_inbox else "Video published!"
        }
    
    async def _get_upload_status(self, publish_id: str) -> Dict[str, Any]:
        """Check upload status."""
        from ..routers.tiktok import load_tokens
        import requests
        
        tokens = load_tokens()
        
        if not tokens or not tokens.get("access_token"):
            return {"success": False, "error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
        response = requests.post(STATUS_URL, headers=headers, json={"publish_id": publish_id})
        
        if response.status_code != 200:
            return {"success": False, "error": response.text}
        
        result = response.json()
        return {
            "success": True,
            "status": result
        }
    
    async def _post_slideshow_to_tiktok(
        self,
        project_id: str,
        caption: str = None
    ) -> Dict[str, Any]:
        """Post project slides as a photo slideshow to TikTok drafts."""
        from .tiktok_poster import TikTokPoster
        
        db = self.get_db()
        try:
            # Get the project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            # Get all slides with completed images
            slides = db.query(Slide).filter(
                Slide.project_id == project_id,
                Slide.final_image_path.isnot(None)
            ).order_by(Slide.order_index).all()
            
            if len(slides) < 2:
                return {
                    "success": False, 
                    "error": f"Need at least 2 slides with images. Found {len(slides)}. Generate images first."
                }
            
            # Collect image paths
            image_paths = [slide.final_image_path for slide in slides]
            
            # Use project topic as caption if not provided
            post_caption = caption or project.topic or project.name or "Philosophy Slideshow"
            
            # Initialize TikTok poster and post
            poster = TikTokPoster()
            
            if not poster.is_authenticated():
                return {
                    "success": False,
                    "error": "TikTok not connected. Please authenticate first using the TikTok auth URL."
                }
            
            result = poster.post_photo_slideshow(
                image_paths=image_paths,
                caption=post_caption,
                to_drafts=True  # Always to drafts
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "project_id": project_id,
                    "publish_id": result.get("publish_id"),
                    "image_count": len(image_paths),
                    "caption": post_caption,
                    "destination": "TikTok Drafts",
                    "message": f"Successfully sent {len(image_paths)} slides to your TikTok drafts! Open TikTok app to edit and publish."
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error posting to TikTok"),
                    "raw_response": result.get("raw_response")
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to post slideshow: {str(e)}"}
        finally:
            db.close()
    
    # -------------------------------------------------------------------------
    # INSTAGRAM TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _check_instagram_status(self) -> Dict[str, Any]:
        """Check Instagram connection status via Post Bridge."""
        from .instagram_poster import InstagramPoster
        
        try:
            poster = InstagramPoster()
            result = poster.check_connection()
            
            if result.get("success"):
                return {
                    "success": True,
                    "connected": True,
                    "username": result.get("username"),
                    "account_id": result.get("account_id"),
                    "platform": "instagram",
                    "service": "Post Bridge"
                }
            else:
                return {
                    "success": False,
                    "connected": False,
                    "error": result.get("error"),
                    "hint": result.get("hint", "Connect your Instagram at https://post-bridge.com/dashboard")
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to check Instagram status: {str(e)}"}
    
    async def _post_slideshow_to_instagram(
        self,
        project_id: str,
        caption: str = None,
        hashtags: List[str] = None
    ) -> Dict[str, Any]:
        """Post project slides as a carousel to Instagram."""
        from .instagram_poster import InstagramPoster
        
        db = self.get_db()
        try:
            # Get the project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            # Get all slides with completed images
            slides = db.query(Slide).filter(
                Slide.project_id == project_id,
                Slide.final_image_path.isnot(None)
            ).order_by(Slide.order_index).all()
            
            if len(slides) < 2:
                return {
                    "success": False, 
                    "error": f"Need at least 2 slides with images. Found {len(slides)}. Generate images first."
                }
            
            # Collect image paths
            image_paths = [slide.final_image_path for slide in slides]
            
            # Use project topic as caption if not provided
            post_caption = caption or project.topic or project.name or "Philosophy Slideshow"
            
            # Default hashtags if none provided
            if hashtags is None:
                hashtags = ["philosophy", "wisdom", "stoicism", "motivation", "mindset"]
            
            # Initialize Instagram poster and post
            poster = InstagramPoster()
            
            # Check connection first
            status = poster.check_connection()
            if not status.get("success"):
                return {
                    "success": False,
                    "error": "Instagram not connected via Post Bridge. Connect at https://post-bridge.com/dashboard"
                }
            
            result = poster.post_carousel(
                image_paths=image_paths,
                caption=post_caption,
                hashtags=hashtags,
                upload_files=True  # Upload local files
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "project_id": project_id,
                    "post_id": result.get("post_id"),
                    "image_count": len(image_paths),
                    "caption": post_caption,
                    "hashtags": hashtags,
                    "destination": "Instagram",
                    "status": result.get("status", "processing"),
                    "message": f"Successfully posted {len(image_paths)} slides to Instagram! Post ID: {result.get('post_id')}"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error posting to Instagram"),
                    "raw_response": result.get("raw_response")
                }
                
        except Exception as e:
            return {"success": False, "error": f"Failed to post to Instagram: {str(e)}"}
        finally:
            db.close()
    
    async def _get_instagram_post_status(self, post_id: str) -> Dict[str, Any]:
        """Check the status of an Instagram post."""
        from .instagram_poster import InstagramPoster
        
        try:
            poster = InstagramPoster()
            
            # Get post status
            status_result = poster.get_post_status(post_id)
            if not status_result.get("success"):
                return status_result
            
            # Get post results (success/failure details)
            results_result = poster.get_post_results(post_id)
            
            response = {
                "success": True,
                "post_id": post_id,
                "status": status_result.get("status"),
                "created_at": status_result.get("created_at"),
                "caption": status_result.get("caption")
            }
            
            # Add results if available
            if results_result.get("success"):
                results = results_result.get("results", [])
                if results:
                    for r in results:
                        platform_data = r.get("platform_data") or {}
                        if platform_data.get("url"):
                            response["instagram_url"] = platform_data.get("url")
                            response["posted"] = True
                        if r.get("error"):
                            response["error"] = r.get("error")
                            response["posted"] = False
            
            return response
            
        except Exception as e:
            return {"success": False, "error": f"Failed to check post status: {str(e)}"}
    
    # -------------------------------------------------------------------------
    # AUTOMATION TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _list_automations(self, status: str = None) -> Dict[str, Any]:
        """List automations."""
        db = self.get_db()
        try:
            query = db.query(Automation)
            if status:
                query = query.filter(Automation.status == status)
            
            automations = query.order_by(Automation.created_at.desc()).all()
            
            return {
                "success": True,
                "automations": [a.to_dict() for a in automations],
                "total": len(automations)
            }
        finally:
            db.close()
    
    async def _create_automation(
        self,
        name: str,
        content_type: str = "wisdom_slideshow",
        image_style: str = "classical",
        topics: List[str] = None,
        schedule_times: List[str] = None,
        schedule_days: List[str] = None
    ) -> Dict[str, Any]:
        """Create an automation."""
        db = self.get_db()
        try:
            automation = Automation(
                name=name,
                content_type=content_type,
                image_style=image_style,
                topics=topics or [],
                schedule_times=schedule_times or [],
                schedule_days=schedule_days or [],
                settings={
                    "auto_approve_script": True,
                    "auto_generate_images": True,
                    "image_model": "gpt15",
                    "font": "social"
                },
                status="stopped",
                is_active=False
            )
            db.add(automation)
            db.commit()
            db.refresh(automation)
            
            return {
                "success": True,
                "automation_id": automation.id,
                "name": automation.name,
                "status": automation.status,
                "message": "Automation created. Call start_automation to activate."
            }
        finally:
            db.close()
    
    async def _start_automation(self, automation_id: str) -> Dict[str, Any]:
        """Start an automation."""
        from .scheduler import get_scheduler
        
        db = self.get_db()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            if not automation:
                return {"success": False, "error": "Automation not found"}
            
            automation.status = "running"
            automation.is_active = True
            db.commit()
            db.refresh(automation)
            
            try:
                scheduler = get_scheduler()
                scheduler.schedule_automation(automation)
            except Exception as e:
                pass  # Log but don't fail
            
            return {
                "success": True,
                "automation_id": automation_id,
                "status": "running",
                "next_run": automation.next_run.isoformat() if automation.next_run else None
            }
        finally:
            db.close()
    
    async def _stop_automation(self, automation_id: str) -> Dict[str, Any]:
        """Stop an automation."""
        from .scheduler import get_scheduler
        
        db = self.get_db()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            if not automation:
                return {"success": False, "error": "Automation not found"}
            
            try:
                scheduler = get_scheduler()
                scheduler.unschedule_automation(automation_id)
            except Exception:
                pass
            
            automation.status = "stopped"
            automation.is_active = False
            automation.next_run = None
            db.commit()
            
            return {
                "success": True,
                "automation_id": automation_id,
                "status": "stopped"
            }
        finally:
            db.close()
    
    async def _run_automation_now(self, automation_id: str) -> Dict[str, Any]:
        """Trigger immediate automation run."""
        from .scheduler import get_scheduler
        
        db = self.get_db()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            if not automation:
                return {"success": False, "error": "Automation not found"}
            
            if not automation.topics:
                return {"success": False, "error": "No topics in queue"}
            
            scheduler = get_scheduler()
            scheduler.run_now(automation_id)
            
            return {
                "success": True,
                "automation_id": automation_id,
                "topic": automation.get_next_topic(),
                "message": "Automation triggered. Check runs for status."
            }
        finally:
            db.close()
    
    async def _add_topics_to_automation(
        self,
        automation_id: str,
        topics: List[str]
    ) -> Dict[str, Any]:
        """Add topics to automation queue."""
        db = self.get_db()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            if not automation:
                return {"success": False, "error": "Automation not found"}
            
            current_topics = automation.topics or []
            current_topics.extend([t.strip() for t in topics if t.strip()])
            automation.topics = current_topics
            db.commit()
            
            return {
                "success": True,
                "automation_id": automation_id,
                "total_topics": len(automation.topics),
                "added": len(topics)
            }
        finally:
            db.close()
    
    async def _get_automation_runs(
        self,
        automation_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get automation run history."""
        db = self.get_db()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            if not automation:
                return {"success": False, "error": "Automation not found"}
            
            runs = db.query(AutomationRun).filter(
                AutomationRun.automation_id == automation_id
            ).order_by(AutomationRun.started_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "automation_id": automation_id,
                "runs": [run.to_dict() for run in runs],
                "total": len(runs)
            }
        finally:
            db.close()
    
    # -------------------------------------------------------------------------
    # SETTINGS TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _list_fonts(self) -> Dict[str, Any]:
        """List available fonts."""
        fonts = [
            {"id": "tiktok", "name": "TikTok Sans", "style": "Official TikTok Font, Clean & Modern"},
            {"id": "tiktok-bold", "name": "TikTok Sans Bold", "style": "Official TikTok Display Font"},
            {"id": "social", "name": "Social (Default)", "style": "Clean, Readable, Sentence Case"},
            {"id": "bebas", "name": "Bebas Neue", "style": "Bold, Impact, All-Caps"},
            {"id": "montserrat", "name": "Montserrat", "style": "Modern, Clean"},
            {"id": "cinzel", "name": "Cinzel", "style": "Classical, Roman"},
            {"id": "oswald", "name": "Oswald", "style": "Condensed, Strong"},
            {"id": "cormorant", "name": "Cormorant", "style": "Elegant, Serif Italic"}
        ]
        
        return {
            "success": True,
            "fonts": fonts,
            "total": len(fonts)
        }
    
    async def _list_content_types(self) -> Dict[str, Any]:
        """List available content types."""
        return {
            "success": True,
            "content_types": list_content_types(),
            "total": len(CONTENT_TYPES)
        }
    
    async def _list_image_styles(self) -> Dict[str, Any]:
        """List available image styles."""
        return {
            "success": True,
            "image_styles": list_image_styles(),
            "total": len(IMAGE_STYLES)
        }
    
    async def _list_themes(self) -> Dict[str, Any]:
        """List available themes."""
        themes = [
            {"id": "golden_dust", "name": "Golden Dust", "description": "Warm golden particles"},
            {"id": "oil_contrast", "name": "Oil Contrast", "description": "High contrast oil painting"},
            {"id": "glitch_titans", "name": "Glitch Titans", "description": "Digital glitch aesthetic"},
            {"id": "scene_portrait", "name": "Scene Portrait", "description": "Dramatic portraits"}
        ]
        
        return {
            "success": True,
            "themes": themes,
            "total": len(themes)
        }
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        from ..config import get_settings
        
        settings = get_settings()
        
        return {
            "success": True,
            "services": {
                "gemini": bool(settings.google_api_key),
                "elevenlabs": bool(settings.elevenlabs_api_key),
                "fal": bool(settings.fal_key),
                "openai": bool(settings.openai_api_key)
            }
        }
    
    # -------------------------------------------------------------------------
    # MEMORY TOOL IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    
    async def _get_session_context(self) -> Dict[str, Any]:
        """Load saved session context."""
        # Memory directory at project root
        memory_dir = Path(__file__).parent.parent.parent.parent / "memory"
        
        result = {
            "success": True,
            "active_project": None,
            "project_details": None,
            "conversation_summary": None,
            "insights": None,
            "recent_learnings": []
        }
        
        try:
            # Load current project
            project_file = memory_dir / "current_project.json"
            if project_file.exists():
                with open(project_file, 'r') as f:
                    data = json.load(f)
                    result["active_project"] = data.get("active_project")
                    result["session_summary"] = data.get("session_summary")
                    result["saved_at"] = data.get("saved_at")
                    
                    # If there's an active project, get its details
                    if result["active_project"]:
                        db = self.get_db()
                        try:
                            project = db.query(Project).filter(
                                Project.id == result["active_project"]
                            ).first()
                            if project:
                                result["project_details"] = {
                                    "id": project.id,
                                    "name": project.name,
                                    "topic": project.topic,
                                    "status": project.status,
                                    "slide_count": len(project.slides)
                                }
                        finally:
                            db.close()
            
            # Load conversation summary
            summary_file = memory_dir / "conversation_summary.txt"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    content = f.read()
                    if "No conversation history" not in content:
                        result["conversation_summary"] = content
            
            # Load insights
            insights_file = memory_dir / "insights.txt"
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    content = f.read()
                    if "None recorded yet" not in content:
                        result["insights"] = content
            
            # Load recent learnings
            learnings_dir = memory_dir / "learnings"
            if learnings_dir.exists():
                for filename in learnings_dir.iterdir():
                    if filename.suffix == '.json':
                        with open(filename, 'r') as f:
                            learnings = json.load(f)
                            # Get last 3 from each category
                            for learning in learnings[-3:]:
                                result["recent_learnings"].append({
                                    "category": filename.stem,
                                    "learning": learning.get("learning"),
                                    "timestamp": learning.get("timestamp")
                                })
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _save_session_context(
        self,
        summary: str,
        project_id: str = None
    ) -> Dict[str, Any]:
        """Save current session context."""
        memory_dir = Path(__file__).parent.parent.parent.parent / "memory"
        memory_dir.mkdir(exist_ok=True)
        
        try:
            # Save current project
            project_file = memory_dir / "current_project.json"
            project_data = {
                "active_project": project_id,
                "session_summary": summary,
                "saved_at": datetime.now().isoformat()
            }
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            # Append to conversation summary (rolling history)
            summary_file = memory_dir / "conversation_summary.txt"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Read existing content
            existing = ""
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    existing = f.read()
            
            # Remove placeholder if present
            if "No conversation history" in existing:
                existing = "# Conversation Summary\n\n"
            
            # Add new entry
            new_entry = f"### [{timestamp}]\n{summary}\n\n"
            
            # Keep last 10 entries (avoid file growing too large)
            entries = existing.split("### [")
            if len(entries) > 10:
                entries = entries[-9:]  # Keep last 9, we'll add 1
                existing = "# Conversation Summary\n\n### [" + "### [".join(entries)
            
            with open(summary_file, 'w') as f:
                f.write(existing + new_entry)
            
            return {
                "success": True,
                "project_id": project_id,
                "summary_saved": True,
                "message": "Session context saved. Will be loaded on next startup."
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _add_agent_insight(
        self,
        category: str,
        insight: str
    ) -> Dict[str, Any]:
        """Add an insight to persistent memory."""
        memory_dir = Path(__file__).parent.parent.parent.parent / "memory"
        insights_file = memory_dir / "insights.txt"
        
        try:
            # Read existing content
            content = ""
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    content = f.read()
            
            # Initialize if empty
            if not content or "# Agent Insights" not in content:
                content = "# Agent Insights\n\n"
            
            # Find or create category section
            category_header = f"## {category}"
            if category_header not in content:
                content += f"\n{category_header}\n\n"
            
            # Remove placeholder
            content = content.replace("(None recorded yet)", "")
            
            # Add insight with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_insight = f"- [{timestamp}] {insight}\n"
            
            # Insert after category header
            parts = content.split(category_header)
            if len(parts) >= 2:
                # Find where to insert (after header and any existing items)
                rest = parts[1]
                # Find next section or end
                next_section = rest.find("\n## ")
                if next_section > 0:
                    # Insert before next section
                    before_next = rest[:next_section].rstrip() + "\n"
                    after_next = rest[next_section:]
                    parts[1] = before_next + new_insight + after_next
                else:
                    # Add at end of section
                    parts[1] = rest.rstrip() + "\n" + new_insight
                content = category_header.join(parts)
            
            with open(insights_file, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "category": category,
                "insight": insight,
                "message": f"Insight saved to '{category}' category."
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Get all tool definitions formatted for Claude API."""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"]
        }
        for tool in TOOL_DEFINITIONS
    ]


def get_tool_categories() -> List[str]:
    """Get all unique tool categories."""
    return list(set(tool.get("category", "other") for tool in TOOL_DEFINITIONS))


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Get tools filtered by category."""
    return [tool for tool in TOOL_DEFINITIONS if tool.get("category") == category]
