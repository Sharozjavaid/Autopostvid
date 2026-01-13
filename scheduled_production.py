#!/usr/bin/env python3
"""
Scheduled Production - Runs content generation at specific times throughout the day.

Schedule (PST) - 9 pieces of content per day:
- 9:00 AM: 1 Slideshow + 1 Narration Video + 1 Video with Transitions
- 1:00 PM: 1 Slideshow + 1 Narration Video + 1 Video with Transitions  
- 5:00 PM: 1 Slideshow + 1 Narration Video + 1 Video with Transitions

Each piece of content is emailed with a caption including #PhilosophizeMeApp

Usage:
    python scheduled_production.py              # Run scheduler
    python scheduled_production.py --test       # Run 1 set immediately (test mode)
    python scheduled_production.py --run 9am    # Run 9 AM set now
    python scheduled_production.py --run 1pm    # Run 1 PM set now
    python scheduled_production.py --run 5pm    # Run 5 PM set now
    python scheduled_production.py --run 1030pm # Run 10:30 PM test set
"""

import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Import production functions
from daily_production import (
    generate_slideshow,
    generate_narration_video,
    generate_video_with_transitions,
    send_slideshow_email,
    send_narration_email,
    send_video_transitions_email,
    log,
    cost_tracker,
    get_next_topic,
    SLIDESHOW_TOPICS_FILE,
    NARRATION_TOPICS_FILE
)

# Schedule times (24-hour format, PST)
# Each time slot runs ALL 3 content types
SCHEDULE = {
    "9am": {
        "hour": 9,
        "minute": 0,
        "description": "Morning Set"
    },
    "1pm": {
        "hour": 13,
        "minute": 0,
        "description": "Afternoon Set"
    },
    "5pm": {
        "hour": 17,
        "minute": 0,
        "description": "Evening Set"
    },
    "1030pm": {
        "hour": 22,
        "minute": 30,
        "description": "Test Set (10:30 PM)"
    },
    "11pm": {
        "hour": 23,
        "minute": 0,
        "description": "Night Test Set (11:00 PM)"
    }
}

# Log file
SCHEDULE_LOG = "scheduled_production.log"


def run_content_set(set_name: str = ""):
    """
    Run a full set of content: 1 Slideshow + 1 Narration + 1 Video Transitions.
    
    This is what runs at each scheduled time.
    """
    log("=" * 60)
    log(f"🚀 RUNNING CONTENT SET: {set_name}")
    log("=" * 60)
    log("   📋 1x Slideshow")
    log("   📋 1x Narration Video")
    log("   📋 1x Video with Transitions")
    log("=" * 60)
    
    results = {
        'slideshow': None,
        'narration': None,
        'video_transitions': None
    }
    
    # 1. Generate Slideshow
    log("\n" + "-" * 40)
    log("🎴 [1/3] GENERATING SLIDESHOW")
    log("-" * 40)
    
    topic = get_next_topic(SLIDESHOW_TOPICS_FILE)
    if topic:
        log(f"📋 Topic: {topic}")
        result = generate_slideshow(topic)
        if result:
            send_slideshow_email(result, topic)
            results['slideshow'] = result
            log("✅ Slideshow complete and emailed!")
        else:
            log("❌ Slideshow failed", "ERROR")
    else:
        log("⚠️ No slideshow topics available!", "WARN")
    
    # 2. Generate Narration Video
    log("\n" + "-" * 40)
    log("🎙️ [2/3] GENERATING NARRATION VIDEO")
    log("-" * 40)
    
    topic = get_next_topic(NARRATION_TOPICS_FILE)
    if topic:
        log(f"📋 Topic: {topic}")
        result = generate_narration_video(topic)
        if result:
            send_narration_email(result, topic)
            results['narration'] = result
            log("✅ Narration video complete and emailed!")
        else:
            log("❌ Narration video failed", "ERROR")
    else:
        log("⚠️ No narration topics available!", "WARN")
    
    # 3. Generate Video with Transitions
    log("\n" + "-" * 40)
    log("🎬 [3/3] GENERATING VIDEO WITH TRANSITIONS")
    log("-" * 40)
    
    # Use narration topics for video transitions (story-style works better)
    topic = get_next_topic(NARRATION_TOPICS_FILE)
    if topic:
        log(f"📋 Topic: {topic}")
        result = generate_video_with_transitions(topic)
        if result:
            send_video_transitions_email(result, topic)
            results['video_transitions'] = result
            log("✅ Video with transitions complete and emailed!")
        else:
            log("❌ Video with transitions failed", "ERROR")
    else:
        log("⚠️ No topics available for video transitions!", "WARN")
    
    # Summary
    log("\n" + "=" * 60)
    log(f"📊 SET COMPLETE: {set_name}")
    log("=" * 60)
    
    success_count = sum(1 for r in results.values() if r is not None)
    log(f"   ✅ Successful: {success_count}/3")
    log(f"   🎴 Slideshow: {'✅' if results['slideshow'] else '❌'}")
    log(f"   🎙️ Narration: {'✅' if results['narration'] else '❌'}")
    log(f"   🎬 Transitions: {'✅' if results['video_transitions'] else '❌'}")
    
    # Print cost summary
    cost_tracker.print_summary()
    
    return results


def get_next_scheduled_time() -> tuple:
    """
    Get the next scheduled time.
    
    Returns:
        Tuple of (datetime, schedule_key, description)
    """
    now = datetime.now()
    
    # Check each scheduled time (excluding 1030pm test - that's manual only)
    candidates = []
    
    for key, sched in SCHEDULE.items():
        # Skip the test slot from automatic scheduling
        if key == "1030pm":
            continue
            
        # Create datetime for today at scheduled time
        scheduled_dt = now.replace(
            hour=sched["hour"],
            minute=sched["minute"],
            second=0,
            microsecond=0
        )
        
        # If this time has passed today, schedule for tomorrow
        if scheduled_dt <= now:
            scheduled_dt += timedelta(days=1)
        
        candidates.append((scheduled_dt, key, sched["description"]))
    
    # Return the nearest scheduled time
    candidates.sort(key=lambda x: x[0])
    return candidates[0]


def run_scheduled_loop():
    """Main scheduling loop - runs forever, triggering content at scheduled times."""
    log("=" * 60)
    log("📅 SCHEDULED PRODUCTION STARTED")
    log("=" * 60)
    log("Schedule (PST) - 9 pieces/day:")
    log("   9:00 AM - 1 Slideshow + 1 Narration + 1 Video")
    log("   1:00 PM - 1 Slideshow + 1 Narration + 1 Video")
    log("   5:00 PM - 1 Slideshow + 1 Narration + 1 Video")
    log("=" * 60)
    
    while True:
        next_time, schedule_key, description = get_next_scheduled_time()
        wait_seconds = (next_time - datetime.now()).total_seconds()
        
        log(f"\n⏰ Next: {description} at {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"   Waiting {wait_seconds/3600:.1f} hours...")
        
        # Wait until scheduled time
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        # Run the content set
        run_content_set(description)
        
        # Small delay to avoid running twice
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Scheduled Content Production")
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run 1 full set immediately (test mode)"
    )
    
    parser.add_argument(
        "--run",
        type=str,
        choices=["9am", "1pm", "5pm", "1030pm", "11pm"],
        help="Run specific time slot content now"
    )
    
    args = parser.parse_args()
    
    # Test mode - run 1 full set immediately
    if args.test:
        log("🧪 TEST MODE: Running 1 full content set")
        run_content_set("Test Run")
        return
    
    # Run specific time slot
    if args.run:
        sched = SCHEDULE.get(args.run)
        if sched:
            log(f"🚀 Running {args.run} content set manually...")
            run_content_set(sched["description"])
        return
    
    # Default: run scheduled loop
    run_scheduled_loop()


if __name__ == "__main__":
    main()
