#!/usr/bin/env python3
import os
import time
import argparse
import random
from dotenv import load_dotenv

# Import our content generation classes
from gemini_handler import GeminiHandler
from smart_image_generator import SmartImageGenerator
from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler
from email_sender import EmailSender

load_dotenv()


# Persistence
TOPICS_FILE = "topics.txt"
COMPLETED_FILE = "completed_topics.txt"
LOG_FILE = "automation.log"

def log_message(message):
    """Log message to file and console"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")

def get_next_topic():
    """Get next topic and remove from list"""
    try:
        if not os.path.exists(TOPICS_FILE):
            return None
            
        with open(TOPICS_FILE, 'r') as f:
            topics = [line.strip() for line in f if line.strip()]
            
        if not topics:
            return None
            
        # Get first topic (FIFO)
        topic = topics[0]
        
        # Rewrite file without this topic
        with open(TOPICS_FILE, 'w') as f:
            f.write("\n".join(topics[1:]) + "\n")
            
        return topic
    except Exception as e:
        log_message(f"Error managing topics: {e}")
        return None

def mark_topic_completed(topic):
    """Add topic to completed list"""
    with open(COMPLETED_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {topic}\n")

def is_within_schedule():
    """Check if current time is within a posting window"""
    # Windows: Morning (8-10), Afternoon (13-15), Evening (18-20)
    current_hour = time.localtime().tm_hour
    
    windows = [
        (8, 10),
        (13, 15),
        (18, 20)
    ]
    
    for start, end in windows:
        if start <= current_hour < end:
            return True
            
    return False

def generate_video_flow(topic: str):
    log_message(f"🚀 STARTING AUTOMATION FOR: '{topic}'")
    
    # Initialize handlers
    try:
        gemini = GeminiHandler()
        img_gen = SmartImageGenerator()
        voice_gen = VoiceGenerator()
        assembler = VideoAssembler()
        email_sender = EmailSender()
    except Exception as e:
        log_message(f"❌ Initialization failed: {e}")
        return None
    
    # 1. Generate Story
    story_data = gemini.generate_philosophy_story(topic)
    
    if not story_data:
        log_message("❌ Script generation failed. Skipping.")
        return None
        
    title = story_data.get('title', topic)
    log_message(f"✅ Script ready: {title}")
    
    # 2. Analyze Scenes & Generate Images
    scenes = story_data.get('scenes', [])
    image_paths = img_gen.generate_all_images(story_data, scenes)
    
    if not image_paths:
        log_message("❌ No images generated. Aborting.")
        return None
            
    # 3. Generate Audio
    # Clean title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    audio_path = voice_gen.generate_voiceover(
        story_data.get('script', ''),
        filename=f"{safe_title}_audio.mp3"
    )
    
    if not audio_path or not os.path.exists(audio_path):
        log_message("❌ Audio generation failed. Aborting.")
        return None
        
    # 4. Assemble Video
    video_path = assembler.create_philosophy_video(
        scenes=scenes,
        audio_path=audio_path,
        image_paths=image_paths,
        story_title=title
    )
    
    if not video_path:
        log_message("❌ Video assembly failed.")
        return None
        
    # 5. Email Video
    subject = f"Philosophy Video: {title}"
    body = f"New video generated for topic: {topic}\n\nTitle: {title}\n\nEnjoy!"
    
    success = email_sender.send_video(video_path, subject=subject, body=body)
    
    if success:
        log_message("✅ Cycle Complete: Video Sent!")
        mark_topic_completed(topic)
    else:
        log_message("⚠️ Cycle Complete: Video created but Email Failed.")
        # Still mark as completed? Yes, video exists.
        mark_topic_completed(topic)
        
    return video_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--smart", action="store_true", help="Run with smart 3x/day scheduling")
    parser.add_argument("--single", type=str, help="Run specific topic")
    args = parser.parse_args()
    
    if args.single:
        generate_video_flow(args.single)
        return

    log_message("🤖 Automation Agent Started")
    
    if args.loop or args.smart:
        while True:
            should_run = False
            
            if args.smart:
                # Check schedule
                if is_within_schedule():
                    # Simple rudimentary check to ensure we don't run 100 times in the window.
                    # Ideally store "last_run_time" in file.
                    # For now, we rely on a long sleep (e.g. 1 hour) so we only hit the window once or twice.
                    log_message("⏰ Time window open! Starting generation...")
                    should_run = True
                else:
                    log_message("💤 Outside schedule window. Sleeping...")
            else:
                # Basic loop
                should_run = True
            
            if should_run:
                topic = get_next_topic()
                if topic:
                    try:
                        generate_video_flow(topic)
                    except Exception as e:
                        log_message(f"🔥 Critical Error: {e}")
                else:
                    log_message("⚠️ No more topics in queue!")
            
            # Sleep logic
            # Smart mode: Check every 30 mins
            # Basic Loop: Check every 1 hour (default)
            sleep_time = 1800 if args.smart else 3600
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()

