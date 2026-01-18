#!/usr/bin/env python3
"""
Content Automations Scheduler

This script runs the pre-written content automations on a schedule:
- 2 runs today (test + production)
- Ongoing schedule: 2 runs per day (10:00 AM and 6:00 PM PST)

Automation Types:
1. NARRATIVE VIDEO: Machiavelli-themed videos with narration + moviepy transitions
2. STATIC SLIDESHOW: Juicy "dangerous man" style slideshows

Both post to TikTok (drafts) and Instagram (direct post).

Usage:
    python run_content_automations.py --run-now          # Run one of each immediately
    python run_content_automations.py --run-narrative    # Run just narrative video
    python run_content_automations.py --run-slideshow    # Run just slideshow
    python run_content_automations.py --schedule         # Start scheduled runs (daemon)
    python run_content_automations.py --test             # Test without posting
"""

import os
import sys
import json
import time
import random
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Event

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from content_automations import (
    ContentAutomationRunner,
    MACHIAVELLI_SCRIPTS,
    DANGEROUS_SLIDESHOW_SCRIPTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Log to file as well
log_file = Path("logs/content_automation.log")
log_file.parent.mkdir(exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)


# =============================================================================
# SCHEDULING CONFIG
# =============================================================================

# Schedule times (24-hour format, PST)
SCHEDULE_TIMES = [
    "10:00",  # 10:00 AM - Morning post
    "18:00",  # 6:00 PM - Evening post
]

# Alternating content types
# Even runs = Narrative Video (Machiavelli)
# Odd runs = Static Slideshow (Dangerous)


# =============================================================================
# TRACKING
# =============================================================================

TRACKING_FILE = Path("content_automation_state.json")


def load_state() -> dict:
    """Load automation state from file."""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE) as f:
            return json.load(f)
    return {
        "total_runs": 0,
        "narrative_runs": 0,
        "slideshow_runs": 0,
        "last_run": None,
        "last_narrative": None,
        "last_slideshow": None,
        "used_scripts": {
            "narrative": [],
            "slideshow": []
        }
    }


def save_state(state: dict):
    """Save automation state to file."""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def get_next_script(script_type: str, state: dict) -> dict:
    """
    Get the next script to use, avoiding recently used ones.
    
    Args:
        script_type: "narrative" or "slideshow"
        state: Current automation state
    """
    if script_type == "narrative":
        scripts = MACHIAVELLI_SCRIPTS
        used_key = "narrative"
    else:
        scripts = DANGEROUS_SLIDESHOW_SCRIPTS
        used_key = "slideshow"
    
    used_titles = state.get("used_scripts", {}).get(used_key, [])
    
    # Filter out recently used scripts
    available = [s for s in scripts if s['title'] not in used_titles]
    
    # If all have been used, reset the list
    if not available:
        state["used_scripts"][used_key] = []
        available = scripts
    
    # Pick random from available
    script = random.choice(available)
    
    # Track this script as used
    if used_key not in state.get("used_scripts", {}):
        state["used_scripts"][used_key] = []
    state["used_scripts"][used_key].append(script['title'])
    
    # Keep only last 3 to allow rotation
    state["used_scripts"][used_key] = state["used_scripts"][used_key][-3:]
    
    return script


# =============================================================================
# RUNNERS
# =============================================================================

def run_narrative_video(post_social: bool = True) -> dict:
    """Run a Machiavelli narrative video generation."""
    state = load_state()
    script = get_next_script("narrative", state)
    
    logger.info(f"🎬 Starting NARRATIVE VIDEO: {script['title']}")
    
    runner = ContentAutomationRunner()
    result = runner.generate_narrative_video(script)
    
    if result.get("success"):
        logger.info(f"✅ Narrative video complete: {result.get('video_path')}")
        
        if post_social:
            logger.info("📱 Posting to social media...")
            post_results = runner.post_to_social(result, post_tiktok=True, post_instagram=True)
            result["social_posts"] = post_results
            
            if post_results.get("tiktok", {}).get("success"):
                logger.info("✅ TikTok: Posted to drafts")
            if post_results.get("instagram", {}).get("success"):
                logger.info("✅ Instagram: Posted!")
        
        # Update state
        state["total_runs"] += 1
        state["narrative_runs"] += 1
        state["last_run"] = datetime.now().isoformat()
        state["last_narrative"] = script['title']
        save_state(state)
    else:
        logger.error(f"❌ Narrative video failed: {result.get('error', 'Unknown error')}")
    
    return result


def run_static_slideshow(post_social: bool = True) -> dict:
    """Run a 'dangerous' static slideshow generation."""
    state = load_state()
    script = get_next_script("slideshow", state)
    
    logger.info(f"🎴 Starting STATIC SLIDESHOW: {script['title']}")
    
    runner = ContentAutomationRunner()
    result = runner.generate_static_slideshow(script)
    
    if result.get("success"):
        logger.info(f"✅ Slideshow complete: {len(result.get('image_paths', []))} slides")
        
        if post_social:
            logger.info("📱 Posting to social media...")
            post_results = runner.post_to_social(result, post_tiktok=True, post_instagram=True)
            result["social_posts"] = post_results
            
            if post_results.get("tiktok", {}).get("success"):
                logger.info("✅ TikTok: Posted to drafts")
            if post_results.get("instagram", {}).get("success"):
                logger.info("✅ Instagram: Posted!")
        
        # Update state
        state["total_runs"] += 1
        state["slideshow_runs"] += 1
        state["last_run"] = datetime.now().isoformat()
        state["last_slideshow"] = script['title']
        save_state(state)
    else:
        logger.error(f"❌ Slideshow failed")
    
    return result


def run_both(post_social: bool = True) -> list:
    """Run both a narrative video and a static slideshow."""
    results = []
    
    logger.info("\n" + "="*60)
    logger.info("RUNNING MACHIAVELLI NARRATIVE VIDEO")
    logger.info("="*60)
    result1 = run_narrative_video(post_social)
    results.append({"type": "narrative", **result1})
    
    # Small delay between runs
    logger.info("\n⏳ Waiting 60 seconds before next generation...")
    time.sleep(60)
    
    logger.info("\n" + "="*60)
    logger.info("RUNNING DANGEROUS SLIDESHOW")
    logger.info("="*60)
    result2 = run_static_slideshow(post_social)
    results.append({"type": "slideshow", **result2})
    
    return results


# =============================================================================
# SCHEDULER
# =============================================================================

class ContentScheduler:
    """Simple scheduler for content automations."""
    
    def __init__(self, schedule_times: list):
        self.schedule_times = schedule_times
        self.stop_event = Event()
        self.run_count = 0
    
    def get_next_run_time(self) -> datetime:
        """Calculate the next scheduled run time."""
        now = datetime.now()
        today = now.date()
        
        for time_str in self.schedule_times:
            hour, minute = map(int, time_str.split(':'))
            scheduled = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            if scheduled > now:
                return scheduled
        
        # All times today have passed, schedule for tomorrow
        hour, minute = map(int, self.schedule_times[0].split(':'))
        tomorrow = today + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time().replace(hour=hour, minute=minute))
    
    def run_scheduled(self):
        """Execute the scheduled content generation."""
        self.run_count += 1
        
        # Alternate between content types
        if self.run_count % 2 == 1:
            logger.info("📅 Scheduled run: NARRATIVE VIDEO")
            run_narrative_video(post_social=True)
        else:
            logger.info("📅 Scheduled run: STATIC SLIDESHOW")
            run_static_slideshow(post_social=True)
    
    def start(self):
        """Start the scheduler loop."""
        logger.info("🚀 Content Scheduler Starting...")
        logger.info(f"   Schedule times: {self.schedule_times}")
        
        while not self.stop_event.is_set():
            next_run = self.get_next_run_time()
            wait_seconds = (next_run - datetime.now()).total_seconds()
            
            logger.info(f"⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M')} ({wait_seconds/3600:.1f} hours)")
            
            # Wait until next run time (check every minute for stop signal)
            while wait_seconds > 0 and not self.stop_event.is_set():
                sleep_time = min(60, wait_seconds)
                time.sleep(sleep_time)
                wait_seconds -= sleep_time
            
            if not self.stop_event.is_set():
                self.run_scheduled()
    
    def stop(self):
        """Stop the scheduler."""
        self.stop_event.set()
        logger.info("🛑 Scheduler stopping...")


def get_run_forecast():
    """Calculate and display run forecast for today, tomorrow, and day after."""
    now = datetime.now()
    today = now.date()
    
    print("\n" + "="*60)
    print("📅 CONTENT AUTOMATION FORECAST")
    print("="*60)
    
    state = load_state()
    print(f"\n📊 Current Stats:")
    print(f"   Total runs: {state.get('total_runs', 0)}")
    print(f"   Narrative videos: {state.get('narrative_runs', 0)}")
    print(f"   Slideshows: {state.get('slideshow_runs', 0)}")
    print(f"   Last run: {state.get('last_run', 'Never')}")
    
    print(f"\n⏰ Schedule: {SCHEDULE_TIMES}")
    print(f"   (Each run alternates between Narrative Video and Slideshow)")
    
    # Calculate upcoming runs
    runs_remaining_today = 0
    for time_str in SCHEDULE_TIMES:
        hour, minute = map(int, time_str.split(':'))
        scheduled = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
        if scheduled > now:
            runs_remaining_today += 1
    
    print(f"\n📆 TODAY ({today.strftime('%A, %B %d')}):")
    print(f"   Scheduled runs remaining: {runs_remaining_today}")
    print(f"   + Test run now: 2 (1 narrative + 1 slideshow)")
    print(f"   = Total today: {runs_remaining_today + 2} posts")
    
    print(f"\n📆 TOMORROW ({(today + timedelta(days=1)).strftime('%A, %B %d')}):")
    print(f"   Scheduled runs: {len(SCHEDULE_TIMES)}")
    
    print(f"\n📆 DAY AFTER ({(today + timedelta(days=2)).strftime('%A, %B %d')}):")
    print(f"   Scheduled runs: {len(SCHEDULE_TIMES)}")
    
    print(f"\n📱 POSTING DESTINATIONS:")
    print(f"   - TikTok: Drafts (you publish manually)")
    print(f"   - Instagram: Direct post to @philosophizeme_app")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Content Automations Scheduler")
    
    parser.add_argument("--run-now", action="store_true", 
                        help="Run one of each automation immediately")
    parser.add_argument("--run-narrative", action="store_true",
                        help="Run just a narrative video")
    parser.add_argument("--run-slideshow", action="store_true",
                        help="Run just a static slideshow")
    parser.add_argument("--schedule", action="store_true",
                        help="Start scheduled runs (daemon mode)")
    parser.add_argument("--test", action="store_true",
                        help="Test mode - generate but don't post to social")
    parser.add_argument("--forecast", action="store_true",
                        help="Show run forecast")
    parser.add_argument("--status", action="store_true",
                        help="Show current automation status")
    
    args = parser.parse_args()
    
    post_social = not args.test
    
    if args.forecast or args.status:
        get_run_forecast()
        return
    
    if args.run_now:
        logger.info("🚀 Running both automations immediately...")
        results = run_both(post_social)
        
        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)
        for r in results:
            status = "✅ SUCCESS" if r.get("success") else "❌ FAILED"
            print(f"{r.get('type', 'unknown').upper()}: {status}")
            if r.get("title"):
                print(f"   Title: {r['title']}")
            if r.get("video_path"):
                print(f"   Video: {r['video_path']}")
            if r.get("image_paths"):
                print(f"   Slides: {len(r['image_paths'])} images")
        return
    
    if args.run_narrative:
        logger.info("🎬 Running narrative video...")
        run_narrative_video(post_social)
        return
    
    if args.run_slideshow:
        logger.info("🎴 Running static slideshow...")
        run_static_slideshow(post_social)
        return
    
    if args.schedule:
        scheduler = ContentScheduler(SCHEDULE_TIMES)
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()
        return
    
    # Default: show help and forecast
    parser.print_help()
    print()
    get_run_forecast()


if __name__ == "__main__":
    main()
