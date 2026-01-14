#!/usr/bin/env python3
"""
Slideshow Generation Pipeline

Automated pipeline for generating TikTok-style philosophy slideshows:
1. Generate script from topic (Gemini)
2. Generate background images (GPT-1.5 via fal.ai)
3. Apply programmatic text overlay (Pillow)
4. Save final slides ready for TikTok/Instagram

Usage:
    python slideshow_pipeline.py "5 Philosophers Who Changed History"
    python slideshow_pipeline.py --topic "Stoic Principles" --font social --slides 6
    python slideshow_pipeline.py --from-file topics.txt --delay 60
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from backend.app.services.gemini_handler import GeminiHandler
from backend.app.services.gpt_image_generator import GPTImageGenerator
from backend.app.services.text_overlay import TextOverlay


class SlideshowPipeline:
    """
    Complete pipeline for generating philosophy slideshows.
    
    Workflow:
    1. Generate script with Gemini (detects list vs narrative style)
    2. Generate clean background images with GPT-1.5
    3. Apply text overlay with Pillow (consistent typography)
    4. Optionally add CTA slide for Philosophize Me app
    5. Output final slides ready for social media
    """
    
    # Available fonts
    FONTS = ["social", "bebas", "montserrat", "cinzel", "oswald", "cormorant"]
    
    # CTA Slide Configuration - always the same
    CTA_CONFIG = {
        "title": "PHILOSOPHIZE ME",
        "subtitle": "Download now on the App Store",
        "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches",
    }
    
    def __init__(
        self,
        output_dir: str = "generated_slideshows",
        font: str = "social",
        image_model: str = "gpt15",
        include_cta: bool = True
    ):
        """
        Initialize the pipeline.
        
        Args:
            output_dir: Base directory for output
            font: Font for text overlay (social, bebas, montserrat, etc.)
            image_model: Image generation model (gpt15, flux)
            include_cta: Add CTA slide for Philosophize Me app at the end
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.font = font if font in self.FONTS else "social"
        self.image_model = image_model
        self.include_cta = include_cta
        
        # Initialize components
        print("🚀 Initializing Slideshow Pipeline...")
        self.gemini = GeminiHandler()
        self.image_gen = GPTImageGenerator(quality="low")
        self.text_overlay = TextOverlay(fonts_dir="fonts", default_style="modern")
        
        print(f"   Font: {self.font}")
        print(f"   Image Model: {self.image_model}")
        print(f"   CTA Slide: {'Enabled' if self.include_cta else 'Disabled'}")
        print(f"   Output: {self.output_dir}")
        print()
    
    def generate_slideshow(
        self,
        topic: str,
        num_slides: int = 6,
        save_metadata: bool = True,
        include_cta: bool = None  # Override instance setting
    ) -> Dict:
        """
        Generate a complete slideshow from a topic.
        
        Args:
            topic: The content topic (e.g., "5 Philosophers Who Changed History")
            num_slides: Number of CONTENT slides (CTA is added after if enabled)
            save_metadata: Save JSON metadata file
            include_cta: Override for including CTA slide (None = use instance setting)
            
        Returns:
            Dict with paths to generated slides and metadata
        """
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine if CTA should be included
        add_cta = include_cta if include_cta is not None else self.include_cta
        
        # Create safe folder name
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_topic = safe_topic.replace(' ', '_')[:50]
        project_dir = self.output_dir / f"{safe_topic}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📝 Generating slideshow: {topic}")
        print(f"   Output: {project_dir}")
        print(f"   CTA Slide: {'Yes' if add_cta else 'No'}")
        print()
        
        # Step 1: Generate script
        print("1️⃣  Generating script...")
        script = self.gemini.generate_slideshow_script(topic)
        
        if not script:
            print("❌ Script generation failed")
            return {"success": False, "error": "Script generation failed"}
        
        slides_data = script.get("slides", [])
        print(f"   ✅ Generated {len(slides_data)} content slides")
        
        # Step 2: Generate background images for content slides
        print("\n2️⃣  Generating background images...")
        backgrounds = []
        
        for i, slide in enumerate(slides_data):
            visual_desc = slide.get("visual_description", "Dark philosophical background")
            
            bg_path = self.image_gen.generate_background(
                visual_description=visual_desc,
                scene_number=i + 1,
                story_title=safe_topic
            )
            
            if bg_path:
                backgrounds.append(bg_path)
                print(f"   ✅ Slide {i + 1}: Background generated")
            else:
                print(f"   ⚠️  Slide {i + 1}: Background failed, using fallback")
                fallback_path = str(project_dir / f"bg_{i + 1}.png")
                self.text_overlay.create_solid_background(fallback_path)
                backgrounds.append(fallback_path)
        
        # Generate CTA background if needed
        cta_bg_path = None
        if add_cta:
            print(f"   🎯 Generating CTA slide background...")
            cta_bg_path = self.image_gen.generate_background(
                visual_description=self.CTA_CONFIG["visual_description"],
                scene_number=len(slides_data) + 1,
                story_title="CTA_Philosophize_Me"
            )
            if not cta_bg_path:
                # Fallback to solid dark background for CTA
                cta_bg_path = str(project_dir / "bg_cta.png")
                self.text_overlay.create_solid_background(cta_bg_path, color=(15, 15, 20))
            print(f"   ✅ CTA background ready")
        
        # Step 3: Apply text overlays to content slides
        print("\n3️⃣  Applying text overlays...")
        final_slides = []
        
        for i, (slide, bg_path) in enumerate(zip(slides_data, backgrounds)):
            output_path = str(project_dir / f"slide_{i}.png")
            
            slide_type = slide.get("slide_type", "content")
            display_text = slide.get("display_text", "")
            subtitle = slide.get("subtitle", "")
            
            try:
                if slide_type == "hook" or i == 0:
                    # Hook slide
                    self.text_overlay.create_hook_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        hook_text=display_text or subtitle,
                        font_name=self.font,
                        style="modern"
                    )
                else:
                    # Content slide (including what would have been "outro" - now just last content)
                    self.text_overlay.create_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        title=display_text,
                        subtitle=subtitle,
                        slide_number=i if i < len(slides_data) - 1 else None,  # No number on last content
                        font_name=self.font,
                        style="modern"
                    )
                
                final_slides.append(output_path)
                print(f"   ✅ Slide {i}: {slide_type}")
                
            except Exception as e:
                print(f"   ❌ Slide {i}: {e}")
        
        # Step 4: Add CTA slide if enabled
        if add_cta and cta_bg_path:
            print("\n4️⃣  Adding CTA slide...")
            cta_output_path = str(project_dir / f"slide_{len(slides_data)}_cta.png")
            
            try:
                self.text_overlay.create_slide(
                    background_path=cta_bg_path,
                    output_path=cta_output_path,
                    title=self.CTA_CONFIG["title"],
                    subtitle=self.CTA_CONFIG["subtitle"],
                    slide_number=None,  # No number on CTA
                    font_name=self.font,
                    style="modern",
                    uppercase_title=True
                )
                final_slides.append(cta_output_path)
                print(f"   ✅ CTA slide added: Download Philosophize Me")
            except Exception as e:
                print(f"   ❌ CTA slide failed: {e}")
        
        # Step 5: Save metadata
        elapsed = time.time() - start_time
        
        result = {
            "success": True,
            "topic": topic,
            "timestamp": timestamp,
            "project_dir": str(project_dir),
            "font": self.font,
            "image_model": self.image_model,
            "include_cta": add_cta,
            "total_slides": len(final_slides),
            "content_slides": len(slides_data),
            "slides": final_slides,
            "backgrounds": backgrounds,
            "script": script,
            "elapsed_seconds": round(elapsed, 1)
        }
        
        if save_metadata:
            metadata_path = project_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📄 Metadata saved: {metadata_path}")
        
        print(f"\n✅ Slideshow complete!")
        print(f"   Content Slides: {len(slides_data)}")
        print(f"   Total Slides: {len(final_slides)}{' (includes CTA)' if add_cta else ''}")
        print(f"   Time: {elapsed:.1f}s")
        print(f"   Location: {project_dir}")
        
        return result
    
    def generate_from_file(
        self,
        topics_file: str,
        delay_seconds: int = 30
    ) -> List[Dict]:
        """
        Generate slideshows from a file of topics (one per line).
        
        Args:
            topics_file: Path to file with topics
            delay_seconds: Delay between generations
            
        Returns:
            List of results for each topic
        """
        with open(topics_file, "r") as f:
            topics = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        print(f"📚 Processing {len(topics)} topics from {topics_file}")
        print(f"   Delay between: {delay_seconds}s")
        print()
        
        results = []
        for i, topic in enumerate(topics):
            print(f"\n{'=' * 60}")
            print(f"📌 Topic {i + 1}/{len(topics)}: {topic}")
            print('=' * 60)
            
            result = self.generate_slideshow(topic)
            results.append(result)
            
            if i < len(topics) - 1:
                print(f"\n⏳ Waiting {delay_seconds}s before next topic...")
                time.sleep(delay_seconds)
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        print(f"\n{'=' * 60}")
        print(f"📊 COMPLETE: {successful}/{len(topics)} slideshows generated")
        print('=' * 60)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate TikTok-style philosophy slideshows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python slideshow_pipeline.py "5 Stoic Philosophers"
  python slideshow_pipeline.py --topic "Ancient Wisdom" --font bebas
  python slideshow_pipeline.py --from-file topics.txt --delay 60
  python slideshow_pipeline.py "3 Life Lessons" --no-cta  # Without CTA slide
        """
    )
    
    parser.add_argument("topic", nargs="?", help="Topic for slideshow")
    parser.add_argument("--topic", "-t", dest="topic_flag", help="Topic (alternative to positional)")
    parser.add_argument("--from-file", "-f", help="Read topics from file (one per line)")
    parser.add_argument("--font", default="social", 
                        choices=["social", "bebas", "montserrat", "cinzel", "oswald", "cormorant"],
                        help="Font for text overlay (default: social)")
    parser.add_argument("--slides", "-n", type=int, default=6, help="Number of content slides (default: 6)")
    parser.add_argument("--output", "-o", default="generated_slideshows", help="Output directory")
    parser.add_argument("--delay", "-d", type=int, default=30, help="Delay between topics in seconds")
    parser.add_argument("--model", default="gpt15", choices=["gpt15", "flux"], help="Image model")
    parser.add_argument("--cta", action="store_true", default=True, 
                        help="Include CTA slide for Philosophize Me app (default: True)")
    parser.add_argument("--no-cta", action="store_true", 
                        help="Disable CTA slide")
    
    args = parser.parse_args()
    
    # Determine topic
    topic = args.topic or args.topic_flag
    
    if not topic and not args.from_file:
        parser.print_help()
        print("\n❌ Error: Please provide a topic or --from-file")
        sys.exit(1)
    
    # Determine CTA setting
    include_cta = not args.no_cta
    
    # Initialize pipeline
    pipeline = SlideshowPipeline(
        output_dir=args.output,
        font=args.font,
        image_model=args.model,
        include_cta=include_cta
    )
    
    # Generate
    if args.from_file:
        results = pipeline.generate_from_file(args.from_file, args.delay)
    else:
        result = pipeline.generate_slideshow(topic, num_slides=args.slides)
        
        # Open output folder on success
        if result.get("success"):
            import subprocess
            subprocess.run(["open", result["project_dir"]], check=False)


if __name__ == "__main__":
    main()
