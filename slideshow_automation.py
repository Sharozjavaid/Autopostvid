#!/usr/bin/env python3
"""
Slideshow Automation Pipeline

This is the main automation runner for generating slideshows.
Supports multiple image models and automation types.

Automation Types:
1. SLIDESHOW: Images with text overlay only (no voice/video)
2. VIDEO_TRANSITIONS: Slideshow + fal.ai video transitions between slides
3. SLIDESHOW_NARRATION: Slideshow + ElevenLabs voiceover
4. FULL_VIDEO: Complete video with narration and transitions

Image Models:
- gpt15: GPT Image 1.5 (detailed, high quality) - RECOMMENDED
- flux: Flux Schnell 1.1 (fast, slightly lower quality)

Usage:
    python slideshow_automation.py --topic "5 philosophers who changed the world"
    python slideshow_automation.py --model flux --type slideshow
    python slideshow_automation.py --compare  # Run both models for comparison
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class AutomationType(str, Enum):
    SLIDESHOW = "slideshow"  # Images + text only
    VIDEO_TRANSITIONS = "video_transitions"  # Slideshow + fal video transitions
    SLIDESHOW_NARRATION = "slideshow_narration"  # Slideshow + voice
    FULL_VIDEO = "full_video"  # Complete video with narration


class ImageModel(str, Enum):
    FLUX = "flux"  # Flux Schnell 1.1
    GPT15 = "gpt15"  # GPT Image 1.5


# Output directories based on model
OUTPUT_DIRS = {
    "flux": "generated_slideshows/flux",
    "gpt15": "generated_slideshows/gpt15",
}

# Log file for tracking
LOG_FILE = "slideshow_automation.log"
COMPLETED_FILE = "completed_slideshows.txt"


def log(message: str, auto_id: str = None):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{auto_id}] " if auto_id else ""
    log_line = f"[{timestamp}] {prefix}{message}"
    print(log_line)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")


def generate_slideshow(
    topic: str,
    model: str = "flux",
    font_name: str = "social",
    visual_style: str = "modern",
    output_dir: str = None,
    auto_id: str = None,
    theme: str = "auto",
    auto_theme: bool = True
) -> Dict:
    """
    Generate a complete slideshow from a topic.
    
    Args:
        topic: The slideshow topic
        model: Image model ("flux" or "gpt15")
        font_name: Font for text overlay ("social", "montserrat", "cinzel", etc.)
        visual_style: Visual style ("modern", "elegant", "bold")
        output_dir: Override output directory
        auto_id: Automation ID for tracking
        theme: Visual theme ("auto", "golden_dust", "glitch_titans", etc.)
        auto_theme: Whether to auto-select theme based on content
    
    Returns:
        Result dictionary with paths and metadata
    """
    # Use themed slideshow if a specific theme is selected
    use_themed = theme != "auto" or auto_theme
    
    if use_themed:
        from themed_slideshow import ThemedSlideshow
        log(f"🎴 Starting THEMED slideshow generation: {topic}", auto_id)
        log(f"   Theme: {theme}, Model: {model}", auto_id)
    else:
        from tiktok_slideshow import TikTokSlideshow
        log(f"🎴 Starting slideshow generation: {topic}", auto_id)
        log(f"   Model: {model}, Font: {font_name}, Style: {visual_style}", auto_id)
    
    # Determine output directory
    if output_dir is None:
        output_dir = OUTPUT_DIRS.get(model, "generated_slideshows")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "backgrounds"), exist_ok=True)
    
    try:
        # Use themed slideshow if theme is specified
        if use_themed:
            themed_slideshow = ThemedSlideshow(
                theme=theme if theme != "auto" else "auto",
                output_dir=output_dir,
                fal_model=model
            )
            
            # Generate using themed pipeline
            result = themed_slideshow.create(topic)
            
            if not result.get('script'):
                log("❌ Failed to generate themed slideshow", auto_id)
                return {"success": False, "error": "Themed slideshow generation failed"}
            
            script = result['script']
            slides = result['slides']
            image_paths = result['image_paths']
            background_paths = result.get('background_paths', [])
            title = script.get('title', topic)
            theme_name = result.get('theme_name', theme)
            
            log(f"   ✅ Themed slideshow generated: {title} ({len(slides)} slides)", auto_id)
            log(f"   🎨 Theme used: {theme_name}", auto_id)
            
            # Calculate safe_name for consistency
            safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]
            safe_name = f"{safe_name}_{model}"
            
        else:
            # Use standard TikTokSlideshow
            # Initialize slideshow generator with specified model
            slideshow = TikTokSlideshow(
                output_dir=output_dir,
                image_generator="fal",
                fal_model=model
            )
            
            # Generate script first
            log("📝 Step 1: Generating script with Gemini...", auto_id)
            script = slideshow._generate_script(topic)
            
            if not script:
                log("❌ Failed to generate script", auto_id)
                return {"success": False, "error": "Script generation failed"}
            
            # Add font/style settings to script
            script['font_name'] = font_name
            script['visual_style'] = visual_style
            
            slides = script.get('slides', [])
            title = script.get('title', topic)
            
            log(f"   ✅ Script generated: {title} ({len(slides)} slides)", auto_id)
            
            # Generate backgrounds
            log(f"🎨 Step 2: Generating {len(slides)} backgrounds with {model}...", auto_id)
            
            safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]
            
            # Add model suffix to distinguish outputs
            safe_name = f"{safe_name}_{model}"
            
            background_paths = []
            for i, slide in enumerate(slides):
                bg_path = slideshow._generate_background(slide, safe_name, i)
                if bg_path:
                    background_paths.append(bg_path)
                    log(f"   ✅ Background {i+1}/{len(slides)} generated", auto_id)
                else:
                    # Fallback to solid background
                    fallback_path = os.path.join(
                        slideshow.backgrounds_dir, 
                        f"{safe_name}_bg_{i}.png"
                    )
                    slideshow._create_fallback_background(fallback_path)
                    background_paths.append(fallback_path)
                    log(f"   ⚠️ Background {i+1}/{len(slides)} fallback used", auto_id)
            
            # Burn text onto images
            log(f"📝 Step 3: Burning text with {font_name} font...", auto_id)
            
            image_paths = []
            for i, slide in enumerate(slides):
                bg_path = background_paths[i] if i < len(background_paths) else background_paths[-1]
                output_path = os.path.join(output_dir, f"{safe_name}_slide_{i}.png")
                
                final_path = slideshow._burn_text_onto_slide(
                    background_path=bg_path,
                    slide=slide,
                    output_path=output_path,
                    font_name=font_name,
                    visual_style=visual_style
                )
                image_paths.append(final_path)
                log(f"   ✅ Slide {i+1}/{len(slides)} complete", auto_id)
        
        # Save script for reference
        script_path = os.path.join(output_dir, f"{safe_name}_script.json")
        with open(script_path, 'w') as f:
            json.dump(script, f, indent=2)
        
        # Log completion
        completion_entry = f"{datetime.now().isoformat()} - {model} - {title}"
        with open(COMPLETED_FILE, 'a') as f:
            f.write(completion_entry + "\n")
        
        log(f"✅ Slideshow complete! {len(image_paths)} slides generated", auto_id)
        log(f"   📁 Output: {output_dir}", auto_id)
        
        result_dict = {
            "success": True,
            "title": title,
            "model": model,
            "font_name": font_name,
            "slides_count": len(image_paths),
            "image_paths": image_paths,
            "background_paths": background_paths,
            "script_path": script_path,
            "output_dir": output_dir
        }
        
        # Add theme info if using themed slideshow
        if use_themed:
            result_dict["theme"] = theme
            result_dict["theme_name"] = theme_name if 'theme_name' in dir() else theme
        
        return result_dict
        
    except Exception as e:
        log(f"❌ Error generating slideshow: {e}", auto_id)
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def compare_models(topic: str, font_name: str = "social") -> Dict:
    """
    Generate the same slideshow with both Flux and GPT15 for comparison.
    
    Args:
        topic: The slideshow topic
        font_name: Font for text overlay
    
    Returns:
        Comparison results with paths for both models
    """
    log("=" * 60)
    log("🔬 MODEL COMPARISON TEST")
    log(f"   Topic: {topic}")
    log(f"   Font: {font_name}")
    log("=" * 60)
    
    results = {}
    
    # Generate with Flux
    log("\n" + "=" * 40)
    log("⚡ FLUX SCHNELL 1.1")
    log("=" * 40)
    flux_result = generate_slideshow(
        topic=topic,
        model="flux",
        font_name=font_name,
        auto_id="FLUX"
    )
    results["flux"] = flux_result
    
    # Generate with GPT15
    log("\n" + "=" * 40)
    log("🎨 GPT IMAGE 1.5")
    log("=" * 40)
    gpt15_result = generate_slideshow(
        topic=topic,
        model="gpt15",
        font_name=font_name,
        auto_id="GPT15"
    )
    results["gpt15"] = gpt15_result
    
    # Summary
    log("\n" + "=" * 60)
    log("📊 COMPARISON SUMMARY")
    log("=" * 60)
    
    for model, result in results.items():
        status = "✅ Success" if result.get("success") else "❌ Failed"
        slides = result.get("slides_count", 0)
        output = result.get("output_dir", "N/A")
        log(f"   {model.upper()}: {status} - {slides} slides")
        log(f"      Output: {output}")
    
    return results


def generate_voice_narration(script_text: str, title: str, output_dir: str, auto_id: str = None) -> Optional[str]:
    """
    Generate voice narration for a script using ElevenLabs.
    
    Args:
        script_text: The text to narrate
        title: Title for the output file
        output_dir: Where to save the audio
        auto_id: Automation ID for tracking
    
    Returns:
        Path to audio file or None if failed
    """
    try:
        from voice_generator import VoiceGenerator
        
        log("🎙️ Generating voice narration...", auto_id)
        
        voice_gen = VoiceGenerator()
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        
        audio_path = voice_gen.generate_voiceover(
            script_text,
            filename=f"{safe_title}_narration.mp3"
        )
        
        if audio_path and os.path.exists(audio_path):
            log(f"   ✅ Voice narration saved: {audio_path}", auto_id)
            return audio_path
        else:
            log("   ❌ Voice generation failed", auto_id)
            return None
            
    except ImportError:
        log("   ⚠️ Voice generator not available", auto_id)
        return None
    except Exception as e:
        log(f"   ❌ Voice generation error: {e}", auto_id)
        return None


def run_automation_loop(
    model: str = "flux",
    automation_type: str = "slideshow",
    font_name: str = "social",
    topics_file: str = "topics.txt",
    auto_id: str = None,
    enable_voice: bool = False,
    enable_video_transitions: bool = False,
    recycle_topics: bool = False,
    theme: str = "auto",
    auto_theme: bool = True
):
    """
    Run continuous automation loop processing topics from file.
    
    Args:
        model: Image model to use
        automation_type: Type of automation
        font_name: Font for text overlay
        topics_file: File with topics (one per line)
        auto_id: Automation ID for tracking
        enable_voice: Whether to generate voice narration
        enable_video_transitions: Whether to add AI video transitions
        recycle_topics: Whether to add completed topics back to queue
        theme: Visual theme for slideshows
        auto_theme: Whether to auto-select theme based on content
    """
    log(f"🚀 Starting automation loop", auto_id)
    log(f"   Model: {model}")
    log(f"   Type: {automation_type}")
    log(f"   Font: {font_name}")
    log(f"   Theme: {theme} (auto: {auto_theme})")
    log(f"   Topics file: {topics_file}")
    log(f"   Voice: {'Enabled' if enable_voice else 'Disabled'}")
    log(f"   Video Transitions: {'Enabled' if enable_video_transitions else 'Disabled'}")
    log(f"   Topic Recycling: {'Enabled' if recycle_topics else 'Disabled'}")
    
    if not os.path.exists(topics_file):
        log(f"❌ Topics file not found: {topics_file}", auto_id)
        return
    
    # Read topics
    with open(topics_file, 'r') as f:
        topics = [line.strip() for line in f if line.strip()]
    
    if not topics:
        log("❌ No topics found in file", auto_id)
        return
    
    log(f"📋 Found {len(topics)} topics to process", auto_id)
    
    processed = 0
    for i, topic in enumerate(topics):
        log(f"\n{'='*60}", auto_id)
        log(f"📌 Processing topic {i+1}/{len(topics)}: {topic}", auto_id)
        log(f"{'='*60}", auto_id)
        
        # Generate slideshow
        result = generate_slideshow(
            topic=topic,
            model=model,
            font_name=font_name,
            auto_id=auto_id,
            theme=theme,
            auto_theme=auto_theme
        )
        
        if result.get("success"):
            processed += 1
            
            # Generate voice narration if enabled
            if enable_voice:
                script_path = result.get("script_path")
                if script_path and os.path.exists(script_path):
                    with open(script_path, 'r') as f:
                        script_data = json.load(f)
                    
                    # Build narration text from slides
                    narration_text = ""
                    for slide in script_data.get('slides', []):
                        narration_text += slide.get('text', '') + " "
                    
                    if narration_text.strip():
                        audio_path = generate_voice_narration(
                            narration_text,
                            result.get('title', topic),
                            result.get('output_dir', 'generated_slideshows'),
                            auto_id
                        )
                        if audio_path:
                            result['audio_path'] = audio_path
            
            # TODO: Add video transitions if enable_video_transitions
            if enable_video_transitions:
                log("⚠️ Video transitions not yet implemented in automation loop", auto_id)
            
            # Mark topic as completed
            completion_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {topic}"
            with open("completed_slideshows.txt", 'a') as f:
                f.write(completion_entry + "\n")
            
            # Recycle topic if enabled (add back to end of queue)
            if recycle_topics:
                with open(topics_file, 'a') as f:
                    f.write(topic + "\n")
                log(f"♻️ Topic recycled back to queue", auto_id)
            
            # Remove topic from front of file
            remaining = topics[i+1:]
            with open(topics_file, 'w') as f:
                for t in remaining:
                    f.write(t + "\n")
    
    log(f"\n✅ Automation complete! Processed {processed}/{len(topics)} topics", auto_id)


def main():
    parser = argparse.ArgumentParser(description="Slideshow Automation Pipeline")
    
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="Single topic to generate"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        choices=["flux", "gpt15"],
        default="gpt15",
        help="Image model to use (default: gpt15)"
    )
    
    parser.add_argument(
        "--type",
        type=str,
        choices=["slideshow", "video_transitions", "slideshow_narration", "full_video"],
        default="slideshow",
        help="Automation type (default: slideshow)"
    )
    
    parser.add_argument(
        "--font",
        type=str,
        default="social",
        help="Font for text overlay (default: social)"
    )
    
    parser.add_argument(
        "--style",
        type=str,
        default="modern",
        help="Visual style (default: modern)"
    )
    
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare both Flux and GPT15 on the same topic"
    )
    
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuous automation from topics.txt"
    )
    
    parser.add_argument(
        "--topics-file",
        type=str,
        default="topics.txt",
        help="File with topics for loop mode"
    )
    
    parser.add_argument(
        "--auto-id",
        type=str,
        help="Automation ID for tracking"
    )
    
    # New voice and video options
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice narration (uses ElevenLabs)"
    )
    
    parser.add_argument(
        "--video-transitions",
        action="store_true",
        help="Enable AI video transitions between slides (uses fal.ai)"
    )
    
    parser.add_argument(
        "--recycle",
        action="store_true",
        help="Recycle completed topics back to queue"
    )
    
    parser.add_argument(
        "--theme",
        type=str,
        default="auto",
        choices=["auto", "golden_dust", "glitch_titans", "oil_contrast", "scene_portrait"],
        help="Visual theme for slideshow generation"
    )
    
    parser.add_argument(
        "--auto-theme",
        action="store_true",
        help="Automatically select theme based on content type"
    )
    
    args = parser.parse_args()
    
    # Comparison mode
    if args.compare:
        if not args.topic:
            print("❌ Please provide a --topic for comparison")
            sys.exit(1)
        
        results = compare_models(args.topic, font_name=args.font)
        
        # Print final paths
        print("\n📁 OUTPUT FILES:")
        for model, result in results.items():
            if result.get("success"):
                print(f"\n{model.upper()}:")
                for path in result.get("image_paths", []):
                    print(f"   {path}")
        
        sys.exit(0)
    
    # Loop mode
    if args.loop:
        run_automation_loop(
            model=args.model,
            automation_type=args.type,
            font_name=args.font,
            topics_file=args.topics_file,
            auto_id=args.auto_id,
            enable_voice=args.voice,
            enable_video_transitions=args.video_transitions,
            recycle_topics=args.recycle,
            theme=args.theme,
            auto_theme=args.auto_theme
        )
        sys.exit(0)
    
    # Single topic mode
    if args.topic:
        result = generate_slideshow(
            topic=args.topic,
            model=args.model,
            font_name=args.font,
            visual_style=args.style,
            auto_id=args.auto_id,
            theme=args.theme,
            auto_theme=args.auto_theme
        )
        
        if result.get("success"):
            print("\n✅ SUCCESS!")
            print(f"   Title: {result.get('title')}")
            print(f"   Model: {result.get('model')}")
            print(f"   Slides: {result.get('slides_count')}")
            print(f"\n📁 Output files:")
            for path in result.get("image_paths", []):
                print(f"   {path}")
            
            # Generate voice if requested for single topic
            if args.voice:
                script_path = result.get("script_path")
                if script_path and os.path.exists(script_path):
                    with open(script_path, 'r') as f:
                        script_data = json.load(f)
                    
                    narration_text = " ".join(
                        slide.get('text', '') for slide in script_data.get('slides', [])
                    )
                    
                    if narration_text.strip():
                        audio_path = generate_voice_narration(
                            narration_text,
                            result.get('title', args.topic),
                            result.get('output_dir', 'generated_slideshows'),
                            args.auto_id
                        )
                        if audio_path:
                            print(f"\n🎙️ Audio: {audio_path}")
        else:
            print(f"\n❌ FAILED: {result.get('error')}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
