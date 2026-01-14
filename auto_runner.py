#!/usr/bin/env python3
import os
import time
import argparse
import random
from dotenv import load_dotenv

# Import our content generation classes
from gemini_handler import GeminiHandler
from unified_image_generator import create_image_generator, UnifiedImageGenerator, ImageModel
from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler
from email_sender import EmailSender
from caption_generator import CaptionGenerator
from fal_video_generator import FalVideoGenerator, check_fal_available

load_dotenv()


# Persistence
TOPICS_FILE = "topics.txt"
COMPLETED_FILE = "completed_topics.txt"
LOG_FILE = "automation.log"

# Default image model for automation (can be overridden via CLI)
DEFAULT_IMAGE_MODEL = "nano"  # Options: "nano", "openai-dalle3", "openai-gpt-image-1.5"

def log_message(message):
    """Log message to file and console"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")

def get_completed_topics():
    """Load set of already-completed topics for deduplication"""
    completed = set()
    try:
        if os.path.exists(COMPLETED_FILE):
            with open(COMPLETED_FILE, 'r') as f:
                for line in f:
                    # Format: "2026-01-09 16:36:22 - Topic Name"
                    if ' - ' in line:
                        topic = line.split(' - ', 1)[1].strip()
                        completed.add(topic.lower())
    except Exception as e:
        log_message(f"Warning: Could not read completed topics: {e}")
    return completed

def get_pending_topics():
    """Load set of topics currently in the queue"""
    pending = set()
    try:
        if os.path.exists(TOPICS_FILE):
            with open(TOPICS_FILE, 'r') as f:
                for line in f:
                    topic = line.strip()
                    if topic:
                        pending.add(topic.lower())
    except Exception as e:
        log_message(f"Warning: Could not read pending topics: {e}")
    return pending

def add_topic(topic: str, allow_duplicates: bool = False) -> bool:
    """
    Add a topic to the queue with deduplication.
    
    Args:
        topic: The topic to add
        allow_duplicates: If False (default), skip topics already completed or pending
        
    Returns:
        True if topic was added, False if skipped as duplicate
    """
    topic = topic.strip()
    if not topic:
        return False
    
    if not allow_duplicates:
        # Check if already completed
        completed = get_completed_topics()
        if topic.lower() in completed:
            log_message(f"⏭️ Topic already completed, not adding: {topic}")
            return False
        
        # Check if already in queue
        pending = get_pending_topics()
        if topic.lower() in pending:
            log_message(f"⏭️ Topic already in queue, not adding: {topic}")
            return False
    
    # Add to queue
    with open(TOPICS_FILE, 'a') as f:
        f.write(topic + "\n")
    log_message(f"✅ Added topic to queue: {topic}")
    return True

def deduplicate_topics_file():
    """
    Clean up topics.txt by removing duplicates and already-completed topics.
    
    Returns:
        Tuple of (topics_removed, topics_remaining)
    """
    try:
        if not os.path.exists(TOPICS_FILE):
            return (0, 0)
        
        with open(TOPICS_FILE, 'r') as f:
            topics = [line.strip() for line in f if line.strip()]
        
        original_count = len(topics)
        
        # Load completed topics
        completed = get_completed_topics()
        
        # Track seen topics for internal deduplication (case-insensitive)
        seen = set()
        unique_topics = []
        
        for topic in topics:
            topic_lower = topic.lower()
            
            # Skip if already completed
            if topic_lower in completed:
                log_message(f"🗑️ Removing completed topic: {topic}")
                continue
            
            # Skip if duplicate within the file
            if topic_lower in seen:
                log_message(f"🗑️ Removing duplicate topic: {topic}")
                continue
            
            seen.add(topic_lower)
            unique_topics.append(topic)
        
        # Rewrite file
        with open(TOPICS_FILE, 'w') as f:
            if unique_topics:
                f.write("\n".join(unique_topics) + "\n")
            else:
                f.write("")
        
        removed = original_count - len(unique_topics)
        log_message(f"🧹 Deduplication complete: removed {removed}, remaining {len(unique_topics)}")
        return (removed, len(unique_topics))
        
    except Exception as e:
        log_message(f"Error deduplicating topics: {e}")
        return (0, 0)

def get_next_topic():
    """Get next topic and remove from list, skipping already-completed topics"""
    try:
        if not os.path.exists(TOPICS_FILE):
            return None
            
        with open(TOPICS_FILE, 'r') as f:
            topics = [line.strip() for line in f if line.strip()]
            
        if not topics:
            return None
        
        # Load completed topics for deduplication
        completed = get_completed_topics()
        
        # Find first topic that hasn't been completed
        topic_to_process = None
        topics_to_skip = []
        
        for i, topic in enumerate(topics):
            if topic.lower() in completed:
                log_message(f"⏭️ Skipping already-completed topic: {topic}")
                topics_to_skip.append(i)
            else:
                topic_to_process = topic
                topics_to_skip.append(i)  # Include this one too since we're processing it
                break
        
        # Remove all skipped/processed topics from the queue
        remaining_topics = [t for i, t in enumerate(topics) if i not in topics_to_skip]
        
        # Rewrite file with remaining topics
        with open(TOPICS_FILE, 'w') as f:
            if remaining_topics:
                f.write("\n".join(remaining_topics) + "\n")
            else:
                f.write("")
        
        if topic_to_process:
            return topic_to_process
        elif topics:
            # All remaining topics were duplicates - recurse to check if more remain
            log_message("All checked topics were duplicates, checking for more...")
            return get_next_topic()
        else:
            return None
            
    except Exception as e:
        log_message(f"Error managing topics: {e}")
        return None

def mark_topic_completed(topic):
    """Add topic to completed list"""
    with open(COMPLETED_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {topic}\n")

def is_within_schedule():
    """Check if current time is within a posting window (PST timezone)"""
    import datetime
    try:
        import pytz
        pst = pytz.timezone('America/Los_Angeles')
        current_hour = datetime.datetime.now(pst).hour
    except ImportError:
        # Fallback: UTC - 8 hours for PST (approximate)
        utc_hour = time.gmtime().tm_hour
        current_hour = (utc_hour - 8) % 24
    
    # Windows in PST: Morning (8-10), Afternoon (13-15), Evening (18-20)
    windows = [
        (8, 10),
        (13, 15),
        (18, 20)
    ]
    
    for start, end in windows:
        if start <= current_hour < end:
            return True
            
    return False

def generate_video_flow(
    topic: str, 
    image_model: str = None, 
    transition: str = "crossfade", 
    transition_duration: float = 0.3,
    use_video_transitions: bool = False,
    fal_resolution: str = "768P",
    clip_duration: str = "6",
    voice_id: str = None
):
    """
    Generate a complete philosophy video from a topic.
    
    Args:
        topic: The philosophy topic to generate content about
        image_model: Image generation model ("nano", "openai-dalle3", "openai-gpt-image-1.5")
        transition: Video transition type ("crossfade", "fade_black", "slide_left", etc.)
        transition_duration: Duration of transitions in seconds
        use_video_transitions: If True, use fal.ai image-to-video instead of static images
        fal_resolution: Resolution for fal.ai video transitions ("768P" or "1080P")
        clip_duration: Duration per clip in seconds ("5" or "6")
        voice_id: ElevenLabs voice ID for narration
    """
    model_name = image_model or DEFAULT_IMAGE_MODEL
    mode_str = "🎬 VIDEO TRANSITIONS" if use_video_transitions else "📸 STATIC IMAGES"
    log_message(f"🚀 STARTING AUTOMATION FOR: '{topic}' [Model: {model_name}] [{mode_str}]")
    
    # Validate fal.ai availability if using video transitions
    if use_video_transitions and not check_fal_available():
        log_message("❌ Video transitions requested but FAL_KEY not set. Falling back to static images.")
        use_video_transitions = False
    
    # Initialize handlers
    try:
        gemini = GeminiHandler()
        img_gen = create_image_generator(model_name)
        voice_gen = VoiceGenerator()
        email_sender = EmailSender()
        caption_gen = CaptionGenerator()
        
        # Only initialize these if NOT using video transitions
        if not use_video_transitions:
            assembler = VideoAssembler()
        else:
            fal_gen = FalVideoGenerator(resolution=fal_resolution)
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
    
    # 2. Analyze Scenes & Generate Images (using unified generator)
    scenes = story_data.get('scenes', [])
    log_message(f"🎨 Generating images with {model_name}...")
    image_paths = img_gen.generate_all_images(story_data, scenes)
    
    if not image_paths:
        log_message("❌ No images generated. Aborting.")
        return None
    
    if use_video_transitions and len(image_paths) < 2:
        log_message("❌ Need at least 2 images for video transitions. Falling back to static.")
        use_video_transitions = False
        assembler = VideoAssembler()
            
    # 3. Generate Audio
    # Clean title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    audio_path = voice_gen.generate_voiceover(
        story_data.get('script', ''),
        voice_id=voice_id,
        filename=f"{safe_title}_audio.mp3"
    )
    
    if not audio_path or not os.path.exists(audio_path):
        log_message("❌ Audio generation failed. Aborting.")
        return None
    
    # 4. Assemble Video
    if use_video_transitions:
        # Use fal.ai image-to-video pipeline
        log_message(f"🎬 Generating AI video transitions ({fal_resolution}, {clip_duration}s clips)...")
        
        # Get scene descriptions for better transition prompts
        scene_descriptions = [s.get('visual_description', '') for s in scenes]
        
        # Generate all transition videos
        video_clip_paths = fal_gen.generate_all_transitions(
            image_paths=image_paths,
            story_title=safe_title,
            scene_descriptions=scene_descriptions,
            duration=clip_duration
        )
        
        if not video_clip_paths:
            log_message("❌ Video transition generation failed.")
            return None
        
        log_message(f"✅ Generated {len(video_clip_paths)} transition clips")
        
        # Combine clips with audio
        log_message("🎬 Creating final video with audio...")
        video_path = fal_gen.create_final_video_with_audio(
            video_paths=video_clip_paths,
            audio_path=audio_path,
            story_title=safe_title,
            crossfade_duration=0.5
        )
    else:
        # Use standard static image assembly
        log_message(f"🎬 Assembling video with {transition} transitions...")
        video_path = assembler.create_philosophy_video(
            scenes=scenes,
            audio_path=audio_path,
            image_paths=image_paths,
            story_title=title,
            transition=transition,
            transition_duration=transition_duration
        )
    
    if not video_path:
        log_message("❌ Video assembly failed.")
        return None
        
    # 5. Generate TikTok Caption
    log_message("📝 Generating TikTok caption...")
    caption = caption_gen.generate_caption(topic, title)
    log_message(f"✅ Caption ready: {caption[:50]}...")
    
    # 6. Email Video with Caption
    mode_label = " (AI Transitions)" if use_video_transitions else ""
    subject = f"Philosophy Video{mode_label}: {title}"
    body = f"New video generated for topic: {topic}\n\nTitle: {title}\n\nMode: {mode_str}\n\nEnjoy!"
    
    success = email_sender.send_video(video_path, subject=subject, body=body, caption=caption)
    
    if success:
        log_message("✅ Cycle Complete: Video Sent!")
        mark_topic_completed(topic)
    else:
        log_message("⚠️ Cycle Complete: Video created but Email Failed.")
        # Still mark as completed? Yes, video exists.
        mark_topic_completed(topic)
        
    return video_path

def main():
    parser = argparse.ArgumentParser(description="Philosophy Video Automation Pipeline")
    parser.add_argument("--loop", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--smart", action="store_true", help="Run with smart 3x/day scheduling")
    parser.add_argument("--single", type=str, help="Run specific topic")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate topics.txt and exit (removes completed and duplicate topics)")
    
    # Image model selection
    parser.add_argument(
        "--image-model", 
        type=str, 
        default=DEFAULT_IMAGE_MODEL,
        choices=["nano", "openai-dalle3", "openai-gpt-image-1.5"],
        help="Image generation model to use (default: nano)"
    )
    
    # Transition options
    parser.add_argument(
        "--transition",
        type=str,
        default="crossfade",
        choices=["none", "crossfade", "fade_black", "slide_left", "slide_right", "slide_up"],
        help="Video transition effect (default: crossfade)"
    )
    parser.add_argument(
        "--transition-duration",
        type=float,
        default=0.3,
        help="Transition duration in seconds (default: 0.3)"
    )
    
    # fal.ai Image-to-Video options
    parser.add_argument(
        "--video-transitions",
        action="store_true",
        help="Use fal.ai image-to-video for cinematic transitions between scenes (requires FAL_KEY)"
    )
    parser.add_argument(
        "--fal-resolution",
        type=str,
        default="768P",
        choices=["768P", "1080P"],
        help="Resolution for fal.ai video transitions (default: 768P, $0.045/sec vs $0.09/sec)"
    )
    parser.add_argument(
        "--clip-duration",
        type=str,
        default="6",
        choices=["5", "6"],
        help="Duration per video clip in seconds (default: 6)"
    )
    parser.add_argument(
        "--voice-id",
        type=str,
        default=None,
        help="ElevenLabs voice ID for narration (default: onwK4e9ZLuTAKqWW03F9)"
    )
    
    args = parser.parse_args()
    
    # Handle dedupe mode first (one-time cleanup)
    if args.dedupe:
        log_message("🧹 Running topic deduplication...")
        removed, remaining = deduplicate_topics_file()
        log_message(f"✅ Done! Removed {removed} duplicates/completed topics. {remaining} topics remaining in queue.")
        return
    
    # Show available models
    available_models = UnifiedImageGenerator.get_available_models()
    log_message(f"📋 Available image models: {[m.value for m in available_models]}")
    log_message(f"🎨 Using image model: {args.image_model}")
    
    if args.video_transitions:
        if check_fal_available():
            log_message(f"🎬 Mode: AI Video Transitions (fal.ai)")
            log_message(f"   Resolution: {args.fal_resolution}")
            log_message(f"   Clip duration: {args.clip_duration}s")
        else:
            log_message("⚠️ FAL_KEY not set, falling back to static image transitions")
            args.video_transitions = False
    
    if not args.video_transitions:
        log_message(f"🎬 Transition: {args.transition} ({args.transition_duration}s)")
    
    if args.single:
        generate_video_flow(
            args.single, 
            image_model=args.image_model,
            transition=args.transition,
            transition_duration=args.transition_duration,
            use_video_transitions=args.video_transitions,
            fal_resolution=args.fal_resolution,
            clip_duration=args.clip_duration,
            voice_id=args.voice_id
        )
        return

    log_message("🤖 Automation Agent Started")
    
    if args.loop or args.smart:
        while True:
            should_run = False
            
            if args.smart:
                # Check schedule
                if is_within_schedule():
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
                        generate_video_flow(
                            topic,
                            image_model=args.image_model,
                            transition=args.transition,
                            transition_duration=args.transition_duration,
                            use_video_transitions=args.video_transitions,
                            fal_resolution=args.fal_resolution,
                            clip_duration=args.clip_duration,
                            voice_id=args.voice_id
                        )
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

