#!/usr/bin/env python3
"""
COMPLETE TEST: Generate both script AND images for mentor-style slideshow

This will:
1. Generate the mentor-style script (JSON)
2. Generate actual slide images using your existing image generation system
3. Save everything to the generated_slideshows folder
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


def test_mentor_script_only():
    """Step 1: Generate just the script"""
    print("=" * 70)
    print("📝 STEP 1: GENERATING MENTOR-STYLE SCRIPT")
    print("=" * 70)
    
    from gemini_handler import GeminiHandler
    
    handler = GeminiHandler()
    
    topic = "Why you can't think clearly"
    print(f"\n🎯 Topic: {topic}")
    print("   Generating script with mentor style...\n")
    
    script = handler.generate_mentor_slideshow(topic)
    
    if script:
        print(f"✅ Script generated!")
        print(f"   Total slides: {script.get('total_slides', 0)}")
        
        # Show preview
        print("\n📋 SLIDE PREVIEW:")
        for slide in script.get('slides', [])[:2]:  # Show first 2 slides
            print(f"\n   Slide {slide['slide_number']} ({slide['slide_type']}):")
            for item in slide['text_items']:
                label = item.get('label', '')
                text = item['text']
                if label:
                    print(f"      {label} {text}")
                else:
                    print(f"      {text}")
        print("      ...")
        
        # Save script
        safe_name = topic.replace(" ", "_").replace("'", "")
        script_file = f"test_mentor_script_{safe_name}.json"
        with open(script_file, "w") as f:
            json.dump(script, f, indent=2)
        print(f"\n💾 Script saved to: {script_file}")
        
        return script
    else:
        print("❌ Failed to generate script")
        return None


def test_mentor_with_images():
    """Step 2: Generate script AND images"""
    print("\n" + "=" * 70)
    print("🎨 STEP 2: GENERATING IMAGES FOR MENTOR SLIDESHOW")
    print("=" * 70)
    
    # Check if we have the necessary API keys
    fal_key = os.getenv('FAL_KEY')
    if not fal_key:
        print("\n⚠️  FAL_KEY not found - cannot generate images")
        print("   The script generation still works, but images require FAL_KEY")
        print("   Add FAL_KEY to your .env file to generate actual images")
        return None
    
    from gemini_handler import GeminiHandler
    from slideshow_generator import SlideshowGenerator
    
    handler = GeminiHandler()
    generator = SlideshowGenerator()
    
    topic = "The truth about your overthinking"
    print(f"\n🎯 Topic: {topic}")
    print("   This will cost ~$0.35-$0.49 (7 slides × $0.05-0.07 per image)\n")
    
    # Step 1: Generate script
    print("📝 Generating mentor-style script...")
    script = handler.generate_mentor_slideshow(topic)
    
    if not script:
        print("❌ Failed to generate script")
        return None
    
    print(f"✅ Script generated ({script.get('total_slides', 0)} slides)")
    
    # Step 2: We need to adapt the script format for the image generator
    # The existing slideshow_generator expects display_text and subtitle
    # But mentor style has multiple text_items per slide
    
    print("\n🔄 Adapting script format for image generation...")
    
    adapted_slides = []
    for slide in script.get('slides', []):
        slide_num = slide['slide_number']
        slide_type = slide['slide_type']
        text_items = slide['text_items']
        visual = slide.get('visual_description', '')
        
        # Combine text items into display_text and subtitle
        if slide_type == 'hook':
            # Hook: Just the main text
            display_text = text_items[0]['text']
            subtitle = ""
        
        elif slide_type == 'content':
            # Content: Main insight as display_text, combine labels as subtitle
            display_text = text_items[0]['text']
            
            # Combine "What it does" and "Why it matters" into subtitle
            what_it_does = ""
            why_it_matters = ""
            
            for item in text_items[1:]:
                label = item.get('label', '')
                text = item['text']
                if 'What it does' in label:
                    what_it_does = f"{label} {text}"
                elif 'Why it matters' in label:
                    why_it_matters = f"{label} {text}"
            
            subtitle = f"{what_it_does}\n\n{why_it_matters}"
        
        elif slide_type == 'outro':
            # Outro: First item as display_text, rest as subtitle
            display_text = text_items[0]['text']
            subtitle_parts = [item['text'] for item in text_items[1:]]
            subtitle = " ".join(subtitle_parts)
        
        adapted_slide = {
            'slide_number': slide_num,
            'slide_type': slide_type,
            'display_text': display_text,
            'subtitle': subtitle,
            'visual_description': visual
        }
        
        adapted_slides.append(adapted_slide)
    
    print(f"✅ Adapted {len(adapted_slides)} slides for image generation")
    
    # Step 3: Generate images
    print("\n🎨 Generating slide images...")
    print("   (This will take 1-2 minutes)")
    
    safe_name = topic.replace(" ", "_").replace("'", "")[:40]
    image_paths = []
    
    for i, slide in enumerate(adapted_slides, 1):
        slide_num = slide['slide_number']
        print(f"\n   [{i}/{len(adapted_slides)}] Generating slide {slide_num} ({slide['slide_type']})...")
        
        try:
            path = generator.generate_slide(slide, f"mentor_{safe_name}")
            if path:
                image_paths.append(path)
                print(f"   ✅ Saved to: {path}")
            else:
                print(f"   ⚠️  Failed to generate slide {slide_num}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Save script with adapted format
    output = {
        'original_script': script,
        'adapted_slides': adapted_slides,
        'image_paths': image_paths
    }
    
    output_file = f"mentor_slideshow_{safe_name}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 70)
    print("🎉 COMPLETE!")
    print("=" * 70)
    print(f"✅ Generated {len(image_paths)}/{len(adapted_slides)} images")
    print(f"📄 Script saved to: {output_file}")
    print(f"🖼️  Images saved to: generated_slideshows/")
    print()
    print("📂 Your files:")
    for path in image_paths:
        print(f"   - {path}")
    
    return output


def show_what_this_does():
    """Explain what happens when you run this"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           MENTOR-STYLE SLIDESHOW: WHAT THIS SCRIPT DOES           ║
╚═══════════════════════════════════════════════════════════════════╝

Option 1: SCRIPT ONLY (Free)
────────────────────────────────────
Run: python test_mentor_full.py --script-only

What it does:
• Generates the mentor-style JSON script
• Shows you the structure (hook + 5 content + outro)
• Saves to test_mentor_script_*.json
• NO images generated
• NO API costs

When to use: Testing the writing style and structure


Option 2: FULL GENERATION (Paid)
────────────────────────────────────
Run: python test_mentor_full.py --full

What it does:
• Generates the mentor-style JSON script
• Converts it to image-compatible format
• Generates 7 actual slide images (via fal.ai)
• Saves images to generated_slideshows/
• Costs: ~$0.35-0.49 (7 slides × $0.05-0.07)

When to use: Creating actual content for posting


REQUIREMENTS:
• Script only: GOOGLE_API_KEY (in .env)
• Full generation: GOOGLE_API_KEY + FAL_KEY (in .env)
    """)


if __name__ == "__main__":
    import sys
    
    print("🎴 MENTOR-STYLE SLIDESHOW GENERATOR TEST")
    
    # Check for arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        show_what_this_does()
        exit(0)
    
    # Check API keys
    google_key = os.getenv('GOOGLE_API_KEY')
    fal_key = os.getenv('FAL_KEY')
    
    print()
    print("API Keys:")
    print(f"  GOOGLE_API_KEY: {'✅ Found' if google_key else '❌ Missing'}")
    print(f"  FAL_KEY: {'✅ Found' if fal_key else '❌ Missing'}")
    print()
    
    if not google_key:
        print("❌ GOOGLE_API_KEY required. Add it to your .env file.")
        exit(1)
    
    # Choose mode
    if "--script-only" in sys.argv:
        # Just generate script
        script = test_mentor_script_only()
        if script:
            print("\n✅ Script generation completed!")
            print("   To generate images, run with --full flag")
    
    elif "--full" in sys.argv:
        # Generate script + images
        if not fal_key:
            print("❌ FAL_KEY required for image generation. Add it to your .env file.")
            print("   Or run with --script-only to just test the script")
            exit(1)
        
        confirm = input("\n⚠️  This will generate 7 images (~$0.35-0.49 cost). Continue? (y/n): ")
        if confirm.lower() == 'y':
            result = test_mentor_with_images()
            if result:
                print("\n✅ Full slideshow generation completed!")
        else:
            print("\n✋ Cancelled")
    
    else:
        # Default: show help
        print("Usage:")
        print("  python test_mentor_full.py --script-only   # Generate script only (free)")
        print("  python test_mentor_full.py --full          # Generate script + images (paid)")
        print("  python test_mentor_full.py --help          # Show detailed info")
        print()
        print("Running script-only mode by default...\n")
        
        script = test_mentor_script_only()
        if script:
            print("\n✅ Done! To generate images, run with --full flag")
