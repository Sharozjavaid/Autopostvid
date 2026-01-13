#!/usr/bin/env python3
"""
Daily Production Runner - Philosophy Content Pipeline

Runs on a schedule to produce:
1. 3x Slideshow + Narration (story-style videos with voiceover)
2. 3x Slideshows Only (list-style content, just images for TikTok carousel)
3. 1x Video with Transitions (image-to-video with AI transitions)

All content is emailed to you when complete.

Cost Tracking:
- Logs all API calls with estimated costs
- Outputs daily cost summary

Usage:
    python daily_production.py                    # Run full daily production
    python daily_production.py --test             # Test run (1 of each type)
    python daily_production.py --type slideshow   # Run only slideshows
    python daily_production.py --type narration   # Run only narration videos
    python daily_production.py --type video       # Run only video transitions
    python daily_production.py --costs            # Show cost summary
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# Import production history for tracking
from production_history import log_production, get_production_history

# =============================================================================
# CONFIGURATION
# =============================================================================

# Daily production counts
DAILY_SLIDESHOWS = 3          # List-style slideshows (no voice)
DAILY_NARRATION_VIDEOS = 3    # Story-style videos with voiceover
DAILY_VIDEO_TRANSITIONS = 1   # Image-to-video with AI transitions

# Image model to use
IMAGE_MODEL = "gpt15"  # GPT Image 1.5

# Topic files
SLIDESHOW_TOPICS_FILE = "topics_list.txt"
NARRATION_TOPICS_FILE = "topics_narration.txt"

# Output directories
SLIDESHOW_OUTPUT_DIR = "generated_slideshows/gpt15"
NARRATION_OUTPUT_DIR = "generated_videos"
VIDEO_TRANSITIONS_DIR = "generated_videos/transitions"

# Cost tracking
COST_LOG_FILE = "cost_tracking.json"
DAILY_LOG_FILE = "daily_production.log"

# Email settings
EMAIL_SUBJECT_PREFIX = "[Philosophy Bot]"

# =============================================================================
# COST ESTIMATES (per API call)
# =============================================================================
COST_ESTIMATES = {
    # Image generation
    "fal_gpt15": 0.02,          # $0.02 per image
    "fal_flux": 0.01,           # $0.01 per image
    "gemini_nano": 0.10,        # $0.10 per image (expensive!)
    "dalle3": 0.04,             # $0.04 per image
    
    # Text/Script generation
    "gemini_script": 0.005,     # $0.005 per script
    
    # Voice generation
    "elevenlabs_voice": 0.03,   # $0.03 per ~30 sec audio
    
    # Video transitions
    "fal_video": 0.15,          # $0.15 per 6-sec transition clip
}


# =============================================================================
# LOGGING & COST TRACKING
# =============================================================================

def log(message: str, level: str = "INFO"):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    with open(DAILY_LOG_FILE, 'a') as f:
        f.write(log_line + "\n")


@dataclass
class CostEntry:
    timestamp: str
    category: str
    operation: str
    count: int
    unit_cost: float
    total_cost: float
    details: str = ""


class CostTracker:
    """Track API costs for all operations."""
    
    def __init__(self):
        self.entries: List[CostEntry] = []
        self._load()
    
    def _load(self):
        """Load existing cost data."""
        if os.path.exists(COST_LOG_FILE):
            try:
                with open(COST_LOG_FILE, 'r') as f:
                    data = json.load(f)
                    self.entries = [CostEntry(**e) for e in data.get('entries', [])]
            except Exception as e:
                log(f"Could not load cost log: {e}", "WARN")
    
    def _save(self):
        """Save cost data to file."""
        try:
            data = {
                'entries': [asdict(e) for e in self.entries],
                'last_updated': datetime.now().isoformat()
            }
            with open(COST_LOG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log(f"Could not save cost log: {e}", "WARN")
    
    def log_cost(self, category: str, operation: str, count: int, 
                 unit_cost: float, details: str = ""):
        """Log a cost entry."""
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            category=category,
            operation=operation,
            count=count,
            unit_cost=unit_cost,
            total_cost=count * unit_cost,
            details=details
        )
        self.entries.append(entry)
        self._save()
        log(f"💰 Cost: ${entry.total_cost:.4f} ({count}x {operation})")
    
    def get_today_costs(self) -> Tuple[float, Dict[str, float]]:
        """Get today's total and breakdown."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_entries = [e for e in self.entries if e.timestamp.startswith(today)]
        
        total = sum(e.total_cost for e in today_entries)
        
        by_category = {}
        for e in today_entries:
            if e.category not in by_category:
                by_category[e.category] = 0
            by_category[e.category] += e.total_cost
        
        return total, by_category
    
    def get_month_costs(self) -> Tuple[float, Dict[str, float]]:
        """Get this month's total and breakdown."""
        month = datetime.now().strftime("%Y-%m")
        month_entries = [e for e in self.entries if e.timestamp.startswith(month)]
        
        total = sum(e.total_cost for e in month_entries)
        
        by_category = {}
        for e in month_entries:
            if e.category not in by_category:
                by_category[e.category] = 0
            by_category[e.category] += e.total_cost
        
        return total, by_category
    
    def print_summary(self):
        """Print cost summary."""
        today_total, today_by_cat = self.get_today_costs()
        month_total, month_by_cat = self.get_month_costs()
        
        print("\n" + "=" * 60)
        print("💰 COST SUMMARY")
        print("=" * 60)
        
        print(f"\n📅 TODAY ({datetime.now().strftime('%Y-%m-%d')}):")
        print(f"   Total: ${today_total:.2f}")
        for cat, cost in today_by_cat.items():
            print(f"   - {cat}: ${cost:.2f}")
        
        print(f"\n📆 THIS MONTH ({datetime.now().strftime('%B %Y')}):")
        print(f"   Total: ${month_total:.2f}")
        for cat, cost in month_by_cat.items():
            print(f"   - {cat}: ${cost:.2f}")
        
        print("\n" + "=" * 60)


# Global cost tracker
cost_tracker = CostTracker()


# =============================================================================
# TOPIC MANAGEMENT
# =============================================================================

def get_next_topic(topics_file: str) -> Optional[str]:
    """Get the next topic from a file and remove it from the queue."""
    if not os.path.exists(topics_file):
        return None
    
    with open(topics_file, 'r') as f:
        lines = f.readlines()
    
    # Find first non-empty, non-comment line
    topic = None
    topic_index = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            topic = stripped
            topic_index = i
            break
    
    if topic is None:
        return None
    
    # Remove topic from file
    remaining = lines[:topic_index] + lines[topic_index + 1:]
    with open(topics_file, 'w') as f:
        f.writelines(remaining)
    
    return topic


def mark_completed(topic: str, content_type: str):
    """Mark a topic as completed."""
    completed_file = f"completed_{content_type}.txt"
    with open(completed_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {topic}\n")


# =============================================================================
# CONTENT GENERATION
# =============================================================================

def generate_slideshow(topic: str) -> Optional[Dict]:
    """Generate a slideshow (list-style, no voice)."""
    log(f"🎴 Generating slideshow: {topic}")
    
    try:
        from tiktok_slideshow import TikTokSlideshow
        
        slideshow = TikTokSlideshow(
            output_dir=SLIDESHOW_OUTPUT_DIR,
            image_generator="fal",
            fal_model=IMAGE_MODEL
        )
        
        result = slideshow.create(topic)
        
        if result.get('image_paths'):
            # Log costs
            num_images = len(result['image_paths'])
            total_cost = num_images * COST_ESTIMATES["fal_gpt15"] + COST_ESTIMATES["gemini_script"]
            
            cost_tracker.log_cost("slideshow", "fal_gpt15", num_images,
                                   COST_ESTIMATES["fal_gpt15"], topic)
            cost_tracker.log_cost("slideshow", "gemini_script", 1,
                                   COST_ESTIMATES["gemini_script"], topic)

            # Log to production history
            title = result.get('script', {}).get('title', topic)
            log_production(
                content_type="slideshow",
                topic=topic,
                title=title,
                image_model=IMAGE_MODEL,
                font_name="social",
                visual_style="modern",
                has_voice=False,
                has_video_transitions=False,
                slides_count=num_images,
                output_files=result['image_paths'],
                estimated_cost=total_cost,
                status="completed"
            )

            mark_completed(topic, "slideshow")
            log(f"✅ Slideshow complete: {num_images} slides")
            return result
        else:
            log(f"❌ Slideshow failed: {topic}", "ERROR")
            return None

    except Exception as e:
        log(f"❌ Slideshow error: {e}", "ERROR")
        return None


def generate_narration_video(topic: str) -> Optional[Dict]:
    """Generate a video with voice narration."""
    log(f"🎙️ Generating narration video: {topic}")
    
    try:
        from gemini_handler import GeminiHandler
        from tiktok_slideshow import TikTokSlideshow
        from voice_generator import VoiceGenerator
        from video_assembler import VideoAssembler
        
        # Step 1: Generate script
        gemini = GeminiHandler()
        story_data = gemini.generate_philosophy_story(topic)
        
        if not story_data:
            log(f"❌ Script generation failed for: {topic}", "ERROR")
            return None
        
        cost_tracker.log_cost("narration", "gemini_script", 1,
                               COST_ESTIMATES["gemini_script"], topic)
        
        # Step 2: Generate images using TikTokSlideshow pipeline
        slideshow = TikTokSlideshow(
            output_dir=f"{NARRATION_OUTPUT_DIR}/slides",
            image_generator="fal",
            fal_model=IMAGE_MODEL
        )
        
        # Convert story scenes to slideshow format
        slides = story_data.get('scenes', [])
        script = {
            'title': story_data.get('title', topic),
            'slides': [
                {
                    'slide_number': i + 1,
                    'slide_type': 'content',
                    'display_text': scene.get('key_concept', ''),
                    'subtitle': scene.get('narration', '')[:80] if scene.get('narration') else '',
                    'visual_description': scene.get('visual_description', '')
                }
                for i, scene in enumerate(slides)
            ]
        }
        
        slide_result = slideshow.create_from_script(script, skip_image_generation=False)
        
        if not slide_result.get('image_paths'):
            log(f"❌ Image generation failed for: {topic}", "ERROR")
            return None
        
        num_images = len(slide_result['image_paths'])
        cost_tracker.log_cost("narration", "fal_gpt15", num_images,
                               COST_ESTIMATES["fal_gpt15"], topic)
        
        # Step 3: Generate voiceover
        voice_gen = VoiceGenerator()
        script_text = story_data.get('script', '')
        
        if not script_text:
            log(f"⚠️ No script text for voiceover", "WARN")
            return None
        
        safe_title = "".join(c for c in story_data.get('title', topic) 
                             if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]
        
        audio_path = voice_gen.generate_voiceover(
            script_text,
            filename=f"{safe_title}_narration.mp3"
        )
        
        if not audio_path or not os.path.exists(audio_path):
            log(f"❌ Voice generation failed for: {topic}", "ERROR")
            return None
        
        cost_tracker.log_cost("narration", "elevenlabs_voice", 1,
                               COST_ESTIMATES["elevenlabs_voice"], topic)
        
        # Step 4: Assemble video
        assembler = VideoAssembler()
        video_path = assembler.create_philosophy_video(
            scenes=slides,
            audio_path=audio_path,
            image_paths=slide_result['image_paths'],
            story_title=story_data.get('title', topic),
            transition="crossfade",
            transition_duration=0.3
        )
        
        if not video_path:
            log(f"❌ Video assembly failed for: {topic}", "ERROR")
            return None

        # Calculate total cost
        num_images = len(slide_result['image_paths'])
        total_cost = (
            num_images * COST_ESTIMATES["fal_gpt15"] +
            COST_ESTIMATES["gemini_script"] +
            COST_ESTIMATES["elevenlabs_voice"]
        )

        # Log to production history
        log_production(
            content_type="narration",
            topic=topic,
            title=story_data.get('title', topic),
            image_model=IMAGE_MODEL,
            font_name="social",
            visual_style="modern",
            has_voice=True,
            has_video_transitions=False,
            slides_count=num_images,
            output_files=slide_result['image_paths'],
            video_path=video_path,
            audio_path=audio_path,
            estimated_cost=total_cost,
            status="completed"
        )

        mark_completed(topic, "narration")
        log(f"✅ Narration video complete: {video_path}")

        return {
            'video_path': video_path,
            'audio_path': audio_path,
            'image_paths': slide_result['image_paths'],
            'title': story_data.get('title', topic),
            'script': story_data
        }

    except Exception as e:
        log(f"❌ Narration video error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


def generate_video_with_transitions(topic: str) -> Optional[Dict]:
    """Generate video with AI image-to-video transitions."""
    log(f"🎬 Generating video with transitions: {topic}")
    
    try:
        from gemini_handler import GeminiHandler
        from tiktok_slideshow import TikTokSlideshow
        from fal_video_generator import FalVideoGenerator
        
        # Step 1: Generate script
        gemini = GeminiHandler()
        story_data = gemini.generate_philosophy_story(topic)
        
        if not story_data:
            log(f"❌ Script generation failed for: {topic}", "ERROR")
            return None
        
        cost_tracker.log_cost("video_transitions", "gemini_script", 1,
                               COST_ESTIMATES["gemini_script"], topic)
        
        # Step 2: Generate images
        slideshow = TikTokSlideshow(
            output_dir=VIDEO_TRANSITIONS_DIR,
            image_generator="fal",
            fal_model=IMAGE_MODEL
        )
        
        slides = story_data.get('scenes', [])
        script = {
            'title': story_data.get('title', topic),
            'slides': [
                {
                    'slide_number': i + 1,
                    'slide_type': 'content',
                    'display_text': scene.get('key_concept', ''),
                    'subtitle': '',
                    'visual_description': scene.get('visual_description', '')
                }
                for i, scene in enumerate(slides)
            ]
        }
        
        slide_result = slideshow.create_from_script(script, skip_image_generation=False)
        
        if not slide_result.get('image_paths'):
            log(f"❌ Image generation failed for: {topic}", "ERROR")
            return None
        
        num_images = len(slide_result['image_paths'])
        cost_tracker.log_cost("video_transitions", "fal_gpt15", num_images,
                               COST_ESTIMATES["fal_gpt15"], topic)
        
        # Step 3: Generate video transitions using fal.ai
        fal_gen = FalVideoGenerator()
        
        safe_title = "".join(c for c in story_data.get('title', topic)
                             if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]
        
        video_clip_paths = fal_gen.generate_all_transitions(
            slide_result['image_paths'],
            safe_title
        )
        
        if not video_clip_paths:
            log(f"❌ Video transitions failed for: {topic}", "ERROR")
            return None
        
        num_transitions = len(video_clip_paths)
        cost_tracker.log_cost("video_transitions", "fal_video", num_transitions,
                               COST_ESTIMATES["fal_video"], topic)
        
        # Step 4: Combine into final video (without audio for now)
        final_video = fal_gen.combine_clips_simple(video_clip_paths, safe_title)

        if not final_video:
            log(f"❌ Video combination failed for: {topic}", "ERROR")
            return None

        # Calculate total cost
        num_images = len(slide_result['image_paths'])
        total_cost = (
            num_images * COST_ESTIMATES["fal_gpt15"] +
            COST_ESTIMATES["gemini_script"] +
            num_transitions * COST_ESTIMATES["fal_video"]
        )

        # Log to production history
        log_production(
            content_type="video_transitions",
            topic=topic,
            title=story_data.get('title', topic),
            image_model=IMAGE_MODEL,
            font_name="social",
            visual_style="modern",
            has_voice=False,
            has_video_transitions=True,
            slides_count=num_images,
            output_files=slide_result['image_paths'] + video_clip_paths,
            video_path=final_video,
            estimated_cost=total_cost,
            status="completed",
            metadata={"transition_clips": len(video_clip_paths)}
        )

        mark_completed(topic, "video_transitions")
        log(f"✅ Video with transitions complete: {final_video}")

        return {
            'video_path': final_video,
            'clip_paths': video_clip_paths,
            'image_paths': slide_result['image_paths'],
            'title': story_data.get('title', topic)
        }

    except Exception as e:
        log(f"❌ Video transitions error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


# =============================================================================
# EMAIL DELIVERY
# =============================================================================

def send_slideshow_email(result: Dict, topic: str) -> bool:
    """Email slideshow images as attachments with caption."""
    try:
        from email_sender import EmailSender
        from caption_generator import CaptionGenerator
        import zipfile

        sender = EmailSender()
        caption_gen = CaptionGenerator()

        # Create a zip of all slides
        title = result.get('script', {}).get('title', topic)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')[:50]

        zip_path = f"{SLIDESHOW_OUTPUT_DIR}/{safe_title}_slides.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            for img_path in result.get('image_paths', []):
                if os.path.exists(img_path):
                    zf.write(img_path, os.path.basename(img_path))

        # Generate caption with hashtags
        caption = caption_gen.generate_caption(topic, title)
        
        # Ensure #PhilosophizeMeApp is included
        if "#PhilosophizeMeApp" not in caption:
            caption = caption.rstrip() + " #PhilosophizeMeApp"

        # Send email with zip and caption
        subject = f"{EMAIL_SUBJECT_PREFIX} Slideshow: {title}"
        body = f"""New TikTok Slideshow Ready!

Topic: {topic}
Title: {title}
Slides: {len(result.get('image_paths', []))}

These slides are ready to be posted as a TikTok carousel.
Just unzip and upload directly to TikTok!

Generated by Philosophy Bot 🤖
"""

        success = sender.send_video(zip_path, subject=subject, body=body, caption=caption)

        if success:
            log(f"📧 Slideshow emailed: {title}")
            log(f"📝 Caption: {caption[:60]}...")

        return success

    except Exception as e:
        log(f"❌ Email error: {e}", "ERROR")
        return False


def send_narration_email(result: Dict, topic: str) -> bool:
    """Email narration video with caption."""
    try:
        from email_sender import EmailSender
        from caption_generator import CaptionGenerator

        sender = EmailSender()
        caption_gen = CaptionGenerator()

        title = result.get('title', topic)
        video_path = result.get('video_path')

        if not video_path or not os.path.exists(video_path):
            log(f"❌ No video to email for: {topic}", "ERROR")
            return False

        # Generate caption with hashtags
        caption = caption_gen.generate_caption(topic, title)
        
        # Ensure #PhilosophizeMeApp is included
        if "#PhilosophizeMeApp" not in caption:
            caption = caption.rstrip() + " #PhilosophizeMeApp"

        subject = f"{EMAIL_SUBJECT_PREFIX} Video: {title}"
        body = f"""New Philosophy Video Ready!

Topic: {topic}
Title: {title}

This video includes voiceover narration and is ready for TikTok.

Generated by Philosophy Bot 🤖
"""

        success = sender.send_video(video_path, subject=subject, body=body, caption=caption)

        if success:
            log(f"📧 Narration video emailed: {title}")
            log(f"📝 Caption: {caption[:60]}...")

        return success

    except Exception as e:
        log(f"❌ Email error: {e}", "ERROR")
        return False


def send_video_transitions_email(result: Dict, topic: str) -> bool:
    """Email video with transitions and caption."""
    try:
        from email_sender import EmailSender
        from caption_generator import CaptionGenerator

        sender = EmailSender()
        caption_gen = CaptionGenerator()

        title = result.get('title', topic)
        video_path = result.get('video_path')

        if not video_path or not os.path.exists(video_path):
            log(f"❌ No video to email for: {topic}", "ERROR")
            return False

        # Generate caption with hashtags
        caption = caption_gen.generate_caption(topic, title)
        
        # Ensure #PhilosophizeMeApp is included
        if "#PhilosophizeMeApp" not in caption:
            caption = caption.rstrip() + " #PhilosophizeMeApp"

        subject = f"{EMAIL_SUBJECT_PREFIX} Video (AI Transitions): {title}"
        body = f"""New Video with AI Transitions Ready!

Topic: {topic}
Title: {title}
Transition clips: {len(result.get('clip_paths', []))}

This video uses AI-generated transitions between scenes for a cinematic effect.

Generated by Philosophy Bot 🤖
"""

        success = sender.send_video(video_path, subject=subject, body=body, caption=caption)

        if success:
            log(f"📧 Video with transitions emailed: {title}")
            log(f"📝 Caption: {caption[:60]}...")

        return success

    except Exception as e:
        log(f"❌ Email error: {e}", "ERROR")
        return False


# =============================================================================
# MAIN PRODUCTION LOOP
# =============================================================================

def run_daily_production(
    num_slideshows: int = DAILY_SLIDESHOWS,
    num_narration: int = DAILY_NARRATION_VIDEOS,
    num_video_transitions: int = DAILY_VIDEO_TRANSITIONS,
    send_emails: bool = True
):
    """Run the full daily production."""
    log("=" * 60)
    log("🚀 STARTING DAILY PRODUCTION")
    log("=" * 60)
    log(f"   Slideshows: {num_slideshows}")
    log(f"   Narration Videos: {num_narration}")
    log(f"   Video Transitions: {num_video_transitions}")
    log(f"   Email Delivery: {'ON' if send_emails else 'OFF'}")
    log("=" * 60)
    
    results = {
        'slideshows': [],
        'narration': [],
        'video_transitions': []
    }
    
    # Generate slideshows
    log("\n" + "=" * 40)
    log("🎴 GENERATING SLIDESHOWS")
    log("=" * 40)
    
    for i in range(num_slideshows):
        topic = get_next_topic(SLIDESHOW_TOPICS_FILE)
        if not topic:
            log(f"⚠️ No more slideshow topics available")
            break
        
        log(f"\n[{i+1}/{num_slideshows}] {topic}")
        result = generate_slideshow(topic)
        
        if result:
            results['slideshows'].append((topic, result))
            if send_emails:
                send_slideshow_email(result, topic)
    
    # Generate narration videos
    log("\n" + "=" * 40)
    log("🎙️ GENERATING NARRATION VIDEOS")
    log("=" * 40)
    
    for i in range(num_narration):
        topic = get_next_topic(NARRATION_TOPICS_FILE)
        if not topic:
            log(f"⚠️ No more narration topics available")
            break
        
        log(f"\n[{i+1}/{num_narration}] {topic}")
        result = generate_narration_video(topic)
        
        if result:
            results['narration'].append((topic, result))
            if send_emails:
                send_narration_email(result, topic)
    
    # Generate video with transitions
    log("\n" + "=" * 40)
    log("🎬 GENERATING VIDEOS WITH TRANSITIONS")
    log("=" * 40)
    
    for i in range(num_video_transitions):
        # Use narration topics for video transitions (story-style works better)
        topic = get_next_topic(NARRATION_TOPICS_FILE)
        if not topic:
            log(f"⚠️ No more topics for video transitions")
            break
        
        log(f"\n[{i+1}/{num_video_transitions}] {topic}")
        result = generate_video_with_transitions(topic)
        
        if result:
            results['video_transitions'].append((topic, result))
            if send_emails:
                send_video_transitions_email(result, topic)
    
    # Summary
    log("\n" + "=" * 60)
    log("📊 DAILY PRODUCTION SUMMARY")
    log("=" * 60)
    log(f"   Slideshows: {len(results['slideshows'])}/{num_slideshows}")
    log(f"   Narration Videos: {len(results['narration'])}/{num_narration}")
    log(f"   Video Transitions: {len(results['video_transitions'])}/{num_video_transitions}")
    
    # Cost summary
    cost_tracker.print_summary()
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Daily Philosophy Content Production")
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test run (1 of each type)"
    )
    
    parser.add_argument(
        "--type",
        type=str,
        choices=["slideshow", "narration", "video"],
        help="Run only a specific content type"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of items to generate (default: 1)"
    )
    
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email delivery"
    )
    
    parser.add_argument(
        "--costs",
        action="store_true",
        help="Show cost summary and exit"
    )
    
    args = parser.parse_args()
    
    # Cost summary only
    if args.costs:
        cost_tracker.print_summary()
        return
    
    # Test mode
    if args.test:
        log("🧪 RUNNING IN TEST MODE (1 of each type)")
        run_daily_production(
            num_slideshows=1,
            num_narration=1,
            num_video_transitions=1,
            send_emails=not args.no_email
        )
        return
    
    # Single type mode
    if args.type:
        count = args.count
        send_emails = not args.no_email
        
        if args.type == "slideshow":
            log(f"🎴 Running {count} slideshows only")
            run_daily_production(count, 0, 0, send_emails)
        elif args.type == "narration":
            log(f"🎙️ Running {count} narration videos only")
            run_daily_production(0, count, 0, send_emails)
        elif args.type == "video":
            log(f"🎬 Running {count} video transitions only")
            run_daily_production(0, 0, count, send_emails)
        return
    
    # Full daily production
    run_daily_production(
        send_emails=not args.no_email
    )


if __name__ == "__main__":
    main()
