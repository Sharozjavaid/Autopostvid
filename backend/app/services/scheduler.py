"""Background scheduler for running automations.

Uses APScheduler to:
1. Check for active automations on startup
2. Schedule jobs based on each automation's schedule_times
3. Run slideshow generation pipeline
4. Post to TikTok if configured
5. Track run history
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy.orm import Session

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ..database import SessionLocal
from ..models import Automation, AutomationRun

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AutomationScheduler:
    """Manages scheduled automation jobs."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one scheduler instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance per job
                'misfire_grace_time': 3600  # 1 hour grace for missed jobs
            }
        )
        self._initialized = True
        self._running = False
        logger.info("AutomationScheduler initialized")
    
    def start(self):
        """Start the scheduler and load active automations."""
        if self._running:
            logger.info("Scheduler already running")
            return
        
        try:
            self.scheduler.start()
            self._running = True
            logger.info("Scheduler started")
            
            # Load all active automations
            self.reload_all_automations()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def reload_all_automations(self):
        """Load all active automations and schedule their jobs."""
        db = SessionLocal()
        try:
            # Get all running automations
            automations = db.query(Automation).filter(
                Automation.status == "running",
                Automation.is_active == True
            ).all()
            
            logger.info(f"Loading {len(automations)} active automations")
            
            for automation in automations:
                self.schedule_automation(automation)
            
        finally:
            db.close()
    
    def schedule_automation(self, automation: Automation):
        """Schedule jobs for an automation based on its schedule_times."""
        job_id_base = f"automation_{automation.id}"
        
        # Remove existing jobs for this automation
        self.unschedule_automation(automation.id)
        
        if not automation.schedule_times:
            logger.info(f"No schedule times for {automation.name}, skipping")
            return
        
        # Parse schedule days (empty = every day)
        days_of_week = automation.schedule_days or []
        if not days_of_week:
            day_str = "*"  # Every day
        else:
            # Convert to cron format (mon, tue, wed, etc.)
            day_map = {
                'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
                'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
            }
            day_str = ",".join(day_map.get(d.lower(), d[:3]) for d in days_of_week)
        
        # Create a job for each scheduled time
        for i, time_str in enumerate(automation.schedule_times):
            try:
                hour, minute = time_str.split(":")
                
                trigger = CronTrigger(
                    hour=int(hour),
                    minute=int(minute),
                    day_of_week=day_str
                )
                
                job_id = f"{job_id_base}_{i}"
                
                self.scheduler.add_job(
                    self.run_automation,
                    trigger=trigger,
                    id=job_id,
                    args=[automation.id],
                    replace_existing=True,
                    name=f"{automation.name} @ {time_str}"
                )
                
                logger.info(f"Scheduled {automation.name} at {time_str} ({day_str})")
                
            except Exception as e:
                logger.error(f"Failed to schedule {automation.name} at {time_str}: {e}")
        
        # Update next_run time
        self._update_next_run(automation.id)
    
    def unschedule_automation(self, automation_id: str):
        """Remove all scheduled jobs for an automation."""
        job_id_base = f"automation_{automation_id}"
        
        jobs_removed = 0
        for job in self.scheduler.get_jobs():
            if job.id.startswith(job_id_base):
                self.scheduler.remove_job(job.id)
                jobs_removed += 1
        
        if jobs_removed:
            logger.info(f"Removed {jobs_removed} jobs for automation {automation_id}")
    
    def _update_next_run(self, automation_id: str):
        """Update the next_run field for an automation."""
        job_id_base = f"automation_{automation_id}"
        
        next_run = None
        for job in self.scheduler.get_jobs():
            if job.id.startswith(job_id_base):
                if job.next_run_time:
                    if next_run is None or job.next_run_time < next_run:
                        next_run = job.next_run_time
        
        if next_run:
            db = SessionLocal()
            try:
                automation = db.query(Automation).filter(Automation.id == automation_id).first()
                if automation:
                    automation.next_run = next_run
                    db.commit()
            finally:
                db.close()
    
    def run_automation(self, automation_id: str):
        """Execute an automation - generate slideshow and optionally post to TikTok."""
        logger.info(f"Running automation {automation_id}")
        
        db = SessionLocal()
        try:
            automation = db.query(Automation).filter(Automation.id == automation_id).first()
            
            if not automation:
                logger.error(f"Automation {automation_id} not found")
                return
            
            if automation.status != "running":
                logger.info(f"Automation {automation.name} is not running, skipping")
                return
            
            # Get the next topic
            topic = automation.get_next_topic()
            settings = automation.settings or {}
            
            # Create run record
            run = AutomationRun(
                automation_id=automation_id,
                topic=topic,
                status="running",
                settings_used={
                    "content_type": automation.content_type,
                    "image_style": automation.image_style,
                    "font": settings.get("font", "social"),
                    "image_model": settings.get("image_model", "gpt15"),
                }
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            
            logger.info(f"Starting run {run.id[:8]} for topic: {topic}")
            
            try:
                # Import and run the slideshow pipeline
                from slideshow_automation import generate_slideshow
                
                result = generate_slideshow(
                    topic=topic,
                    model=settings.get("image_model", "gpt15"),
                    font_name=settings.get("font", "social"),
                    theme=automation.image_style or "auto",
                    auto_id=automation.name[:20]
                )
                
                if result.get("success"):
                    run.mark_completed(
                        slides_count=result.get("slides_count", 0),
                        image_paths=result.get("image_paths", [])
                    )
                    run.script_path = result.get("script_path")
                    
                    logger.info(f"Run {run.id[:8]} completed: {result.get('slides_count')} slides")
                    
                    # Post to TikTok if enabled
                    if settings.get("post_to_tiktok", False):
                        self._post_to_tiktok(run, result, db)
                    
                    # Update automation stats
                    automation.successful_runs += 1
                    automation.advance_topic()
                    
                else:
                    run.mark_failed(result.get("error", "Unknown error"))
                    automation.failed_runs += 1
                    logger.error(f"Run {run.id[:8]} failed: {result.get('error')}")
                
            except Exception as e:
                run.mark_failed(str(e), {"traceback": str(e)})
                automation.failed_runs += 1
                logger.exception(f"Run {run.id[:8]} exception: {e}")
            
            # Update automation
            automation.total_runs += 1
            automation.last_run = datetime.utcnow()
            db.commit()
            
            # Update next run time
            self._update_next_run(automation_id)
            
        except Exception as e:
            logger.exception(f"Error running automation {automation_id}: {e}")
        finally:
            db.close()
    
    def _post_to_tiktok(self, run: AutomationRun, result: dict, db: Session):
        """Post the generated slideshow to TikTok."""
        try:
            from ..services.tiktok_poster import TikTokPoster
            
            poster = TikTokPoster()
            
            image_paths = result.get("image_paths", [])
            if not image_paths:
                run.tiktok_error = "No images to post"
                return
            
            # Generate caption from topic
            title = result.get("title", run.topic)
            caption = f"{title} #philosophy #stoicism #wisdom #motivation"
            
            # Post as photo slideshow
            post_result = poster.post_photo_slideshow(
                image_paths=image_paths,
                caption=caption
            )
            
            if post_result.get("success"):
                run.mark_posted(post_result.get("publish_id", ""))
                logger.info(f"Posted to TikTok: {post_result.get('publish_id')}")
            else:
                run.tiktok_error = post_result.get("error", "Unknown TikTok error")
                run.tiktok_post_status = "failed"
                logger.error(f"TikTok post failed: {run.tiktok_error}")
            
            db.commit()
            
        except Exception as e:
            run.tiktok_error = str(e)
            run.tiktok_post_status = "failed"
            db.commit()
            logger.exception(f"TikTok posting error: {e}")
    
    def run_now(self, automation_id: str):
        """Trigger an immediate run of an automation (for testing)."""
        thread = Thread(target=self.run_automation, args=(automation_id,))
        thread.start()
        return thread
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return {
            "running": self._running,
            "job_count": len(jobs),
            "jobs": jobs
        }


# Global scheduler instance
scheduler = AutomationScheduler()


def get_scheduler() -> AutomationScheduler:
    """Get the global scheduler instance."""
    return scheduler
