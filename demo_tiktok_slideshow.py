#!/usr/bin/env python3
"""
Demo: TikTok Slideshow Generator

This demo shows the complete workflow for creating TikTok-style slideshows:
1. AI generates text content (Gemini)
2. AI generates background images (fal.ai or OpenAI)
3. Text is burned onto images programmatically (Pillow)

Run this to see the system in action:
    python demo_tiktok_slideshow.py

Options:
    --topic "Your topic here"     Custom topic
    --test                        Use solid backgrounds (no image API calls)
    --preview                     Just generate and preview the script
"""

import argparse
import os
import sys


def demo_text_overlay():
    """Demo 1: Just the text overlay functionality (no AI)"""
    print("\n" + "=" * 60)
    print("📝 DEMO 1: Text Overlay (No AI)")
    print("=" * 60)
    print("This shows how text is burned onto images.\n")
    
    from text_overlay import TextOverlay
    
    overlay = TextOverlay()
    
    # Create output directory
    output_dir = "demo_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a gradient background
    bg_path = f"{output_dir}/demo_background.png"
    overlay.create_solid_background(bg_path, color=(20, 30, 45), gradient=True)
    print(f"✅ Created gradient background: {bg_path}")
    
    # Create hook slide (like the image you showed)
    hook_path = f"{output_dir}/demo_hook.png"
    overlay.create_hook_slide(
        background_path=bg_path,
        output_path=hook_path,
        hook_text="6 philosophical practices successful people use daily to find inner peace"
    )
    print(f"✅ Created hook slide: {hook_path}")
    
    # Create content slides
    content_slides = [
        {
            "title": "MORNING MEDITATION",
            "subtitle": "Start each day with 10 minutes of silence. Your mind will thank you.",
            "number": 1
        },
        {
            "title": "STOIC JOURNALING",
            "subtitle": "Write down what you can control. Let go of everything else.",
            "number": 2
        },
        {
            "title": "NEGATIVE VISUALIZATION",
            "subtitle": "Imagine losing what you have. Suddenly, you'll appreciate everything.",
            "number": 3
        }
    ]
    
    for slide in content_slides:
        output_path = f"{output_dir}/demo_slide_{slide['number']}.png"
        overlay.create_slide(
            background_path=bg_path,
            output_path=output_path,
            title=slide["title"],
            subtitle=slide["subtitle"],
            slide_number=slide["number"]
        )
    
    print(f"\n🎉 Demo complete! Check the '{output_dir}/' folder for output images.")
    print("   These show text burned onto solid backgrounds.")


def demo_full_pipeline(topic: str, test_mode: bool = False):
    """Demo 2: Full pipeline with AI"""
    print("\n" + "=" * 60)
    print("🎴 DEMO 2: Full TikTok Slideshow Pipeline")
    print("=" * 60)
    print(f"Topic: {topic}")
    print(f"Mode: {'TEST (solid backgrounds)' if test_mode else 'FULL (AI backgrounds)'}\n")
    
    from tiktok_slideshow import TikTokSlideshow
    
    slideshow = TikTokSlideshow()
    result = slideshow.create(topic, skip_image_generation=test_mode)
    
    if result['image_paths']:
        print(f"\n🎉 Success! Created {len(result['image_paths'])} slides")
        print("\n📁 Output files:")
        for path in result['image_paths']:
            print(f"   - {path}")
        
        if result.get('script_path'):
            print(f"\n📄 Script saved to: {result['script_path']}")
            print("   (Edit this JSON and re-run with create_from_script() for tweaks)")
    else:
        print("\n❌ Failed to create slideshow")
    
    return result


def demo_script_preview(topic: str):
    """Demo 3: Preview script without generating images"""
    print("\n" + "=" * 60)
    print("📋 DEMO 3: Script Preview (No Image Generation)")
    print("=" * 60)
    print(f"Topic: {topic}\n")
    
    from tiktok_slideshow import TikTokSlideshow
    
    slideshow = TikTokSlideshow()
    script = slideshow.preview_script(topic)
    
    return script


def demo_with_real_background():
    """Demo 4: Use an existing image as background"""
    print("\n" + "=" * 60)
    print("🖼️ DEMO 4: Using Existing Image as Background")
    print("=" * 60)
    
    from text_overlay import TextOverlay
    
    overlay = TextOverlay()
    
    # Check for any existing image in generated_images
    import glob
    existing_images = glob.glob("generated_images/*.png")
    
    if existing_images:
        bg_path = existing_images[0]
        print(f"Using existing image: {bg_path}")
        
        output_path = "demo_output/demo_real_bg.png"
        os.makedirs("demo_output", exist_ok=True)
        
        overlay.create_slide(
            background_path=bg_path,
            output_path=output_path,
            title="MARCUS AURELIUS",
            subtitle="The most powerful man on Earth asked himself every night: 'Was I a good person today?'",
            slide_number=1
        )
        print(f"✅ Created slide with real background: {output_path}")
    else:
        print("No existing images found in generated_images/")
        print("Run with --test first to generate some images, or add your own.")


def main():
    parser = argparse.ArgumentParser(
        description="Demo TikTok Slideshow Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Just test text overlay (no AI, fastest)
    python demo_tiktok_slideshow.py --overlay-only
    
    # Full pipeline with solid backgrounds (test mode)
    python demo_tiktok_slideshow.py --test
    
    # Preview script only (no images)
    python demo_tiktok_slideshow.py --preview
    
    # Full pipeline with AI backgrounds
    python demo_tiktok_slideshow.py
    
    # Custom topic
    python demo_tiktok_slideshow.py --topic "5 Stoic quotes for tough times"
        """
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        default="6 philosophical practices successful people use daily to find inner peace",
        help="Topic for the slideshow"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use solid backgrounds instead of AI-generated images"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Only generate and preview the script (no images)"
    )
    parser.add_argument(
        "--overlay-only",
        action="store_true",
        help="Only demo the text overlay (no AI at all)"
    )
    parser.add_argument(
        "--use-existing",
        action="store_true",
        help="Demo using an existing image as background"
    )
    
    args = parser.parse_args()
    
    print("🎴 TikTok Slideshow Generator Demo")
    print("=" * 60)
    
    if args.overlay_only:
        demo_text_overlay()
    elif args.use_existing:
        demo_with_real_background()
    elif args.preview:
        demo_script_preview(args.topic)
    else:
        demo_full_pipeline(args.topic, test_mode=args.test)
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
