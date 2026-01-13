#!/usr/bin/env python3
"""
Schedule Production - Runs daily production at scheduled times.

This script runs continuously and triggers daily_production.py at the configured time.

Usage:
    python schedule_production.py              # Run scheduler (default: 8 AM PST)
    python schedule_production.py --time 10:00 # Run at 10:00 AM local time
    python schedule_production.py --now        # Run immediately, then continue scheduling
"""

import os
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Default schedule time (PST)
DEFAULT_RUN_TIME = "08:00"  # 8:00 AM

# Log file
SCHEDULE_LOG = "schedule.log"


def log(message: str):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(SCHEDULE_LOG, 'a') as f:
        f.write(log_line + "\n")


def get_next_run_time(run_time_str: str) -> datetime:
    """Calculate the next run time."""
    now = datetime.now()
    run_hour, run_minute = map(int, run_time_str.split(':'))
    
    next_run = now.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
    
    # If we've passed today's run time, schedule for tomorrow
    if now >= next_run:
        next_run += timedelta(days=1)
    
    return next_run


def run_daily_production():
    """Execute the daily production script."""
    log("🚀 Starting daily production...")
    
    try:
        result = subprocess.run(
            ["python3", "daily_production.py"],
            capture_output=True,
            text=True,
            timeout=3600 * 4  # 4 hour timeout
        )
        
        if result.returncode == 0:
            log("✅ Daily production completed successfully")
        else:
            log(f"❌ Daily production failed with code {result.returncode}")
            log(f"   stderr: {result.stderr[:500]}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        log("❌ Daily production timed out (4 hours)")
        return False
    except Exception as e:
        log(f"❌ Error running daily production: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Schedule Daily Production")
    
    parser.add_argument(
        "--time",
        type=str,
        default=DEFAULT_RUN_TIME,
        help=f"Time to run daily (HH:MM, default: {DEFAULT_RUN_TIME})"
    )
    
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run immediately, then continue with schedule"
    )
    
    args = parser.parse_args()
    
    log("=" * 60)
    log("📅 DAILY PRODUCTION SCHEDULER")
    log("=" * 60)
    log(f"   Scheduled time: {args.time}")
    log(f"   Run now: {args.now}")
    log("=" * 60)
    
    # Run immediately if requested
    if args.now:
        log("▶️ Running immediately as requested...")
        run_daily_production()
    
    # Main scheduling loop
    while True:
        next_run = get_next_run_time(args.time)
        wait_seconds = (next_run - datetime.now()).total_seconds()
        
        log(f"⏰ Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"   Waiting {wait_seconds/3600:.1f} hours...")
        
        # Wait until run time
        time.sleep(wait_seconds)
        
        # Run production
        run_daily_production()
        
        # Small delay to avoid running twice
        time.sleep(60)


if __name__ == "__main__":
    main()
