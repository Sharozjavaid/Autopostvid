#!/usr/bin/env python3
"""
Test Script for Unified Content + Template Image System

This tests the new consolidated approach:
1. UnifiedContentGenerator - ONE prompt for all content types
2. TemplateImageGenerator - Consistent visual styles via templates

Usage:
    python test_unified_system.py                    # Run all tests
    python test_unified_system.py --content-only     # Test content generation only
    python test_unified_system.py --image-only       # Test image generation only
    python test_unified_system.py --template TEMPLATE_ID  # Test specific template
    python test_unified_system.py --full TOPIC       # Full pipeline test
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv()


def test_content_generation():
    """Test the unified content generator with different topic types"""
    
    print("\n" + "=" * 60)
    print("📝 TESTING UNIFIED CONTENT GENERATOR")
    print("=" * 60)
    
    from unified_content_generator import UnifiedContentGenerator
    
    generator = UnifiedContentGenerator()
    
    test_topics = [
        # List-style (should detect as "list")
        "5 philosophers who mastered inner peace",
        
        # Narrative (should detect as "narrative")
        "The day Socrates chose death over silence",
        
        # Lessons/Argument (should detect as "lessons")
        "Why ancient philosophy is better than modern therapy"
    ]
    
    results = []
    
    for topic in test_topics:
        print(f"\n{'─' * 50}")
        print(f"📌 Topic: {topic}")
        print('─' * 50)
        
        result = generator.generate_content(topic, num_slides=6)
        
        if result:
            print(f"\n✅ SUCCESS")
            print(f"   Title: {result.get('title')}")
            print(f"   Content Type: {result.get('content_type')}")
            print(f"   Hook: {result.get('hook', '')[:60]}...")
            
            slides = result.get('slides', [])
            print(f"   Slides: {len(slides)}")
            
            # Validate slide structure
            valid = True
            for slide in slides:
                if not slide.get('display_text'):
                    print(f"   ⚠️  Slide {slide.get('slide_number')} missing display_text")
                    valid = False
                if not slide.get('visual_description'):
                    print(f"   ⚠️  Slide {slide.get('slide_number')} missing visual_description")
                    valid = False
            
            if valid:
                print(f"   ✅ All slides have required fields")
            
            # Show first and last slide
            if slides:
                print(f"\n   First Slide (Hook):")
                first = slides[0]
                print(f"     display_text: {first.get('display_text')}")
                print(f"     visual: {first.get('visual_description', '')[:50]}...")
                
                print(f"\n   Last Slide (Outro):")
                last = slides[-1]
                print(f"     display_text: {last.get('display_text')}")
            
            results.append({"topic": topic, "success": True, "content_type": result.get('content_type')})
            
            # Save result for inspection
            safe_topic = "".join(c for c in topic if c.isalnum() or c == ' ')[:30].replace(' ', '_')
            output_file = f"test_output_{safe_topic}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n   📄 Saved to: {output_file}")
        else:
            print(f"\n❌ FAILED to generate content")
            results.append({"topic": topic, "success": False})
    
    # Summary
    print("\n" + "=" * 60)
    print("CONTENT GENERATION SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ {success_count}/{len(results)} topics generated successfully")
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        content_type = r.get('content_type', 'unknown')
        print(f"   {status} {r['topic'][:40]}... ({content_type})")
    
    return results


def test_image_templates():
    """Test the template-based image generator"""
    
    print("\n" + "=" * 60)
    print("🎨 TESTING TEMPLATE IMAGE GENERATOR")
    print("=" * 60)
    
    # Check for FAL_KEY
    if not os.getenv('FAL_KEY'):
        print("❌ FAL_KEY not found in .env - skipping image tests")
        print("   Set FAL_KEY to enable image generation tests")
        return []
    
    from template_image_generator import TemplateImageGenerator, TEMPLATES
    
    # List available templates
    print("\n📋 Available Templates:")
    for tid, template in TEMPLATES.items():
        print(f"   - {tid}: {template['name']}")
    
    # Test with first template only (to save API costs)
    test_template = "classical_renaissance"
    
    print(f"\n{'─' * 50}")
    print(f"🎨 Testing template: {test_template}")
    print('─' * 50)
    
    gen = TemplateImageGenerator(model="gpt-image-1")
    
    # Test different slide types
    test_slides = [
        {
            "display_text": "5 MINDS THAT MASTERED PEACE",
            "slide_type": "hook",
            "person_name": None
        },
        {
            "display_text": "MARCUS AURELIUS",
            "slide_type": "person",
            "person_name": "Marcus Aurelius"
        },
        {
            "display_text": "CONTROL WHAT YOU CAN",
            "slide_type": "lesson",
            "person_name": None
        }
    ]
    
    results = []
    
    for i, slide in enumerate(test_slides):
        print(f"\n📷 Generating slide {i}: {slide['display_text']}")
        
        path = gen.generate_slide(
            template_id=test_template,
            slide_data=slide,
            slide_number=i,
            title="template_test",
            include_text=True
        )
        
        if path:
            results.append({"slide": i, "success": True, "path": path})
            print(f"   ✅ Saved: {path}")
        else:
            results.append({"slide": i, "success": False})
            print(f"   ❌ Failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("IMAGE GENERATION SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ {success_count}/{len(results)} slides generated successfully")
    
    return results


def test_full_pipeline(topic: str, template_id: str = "classical_renaissance"):
    """Test the full pipeline: content generation -> image generation"""
    
    print("\n" + "=" * 60)
    print("🚀 FULL PIPELINE TEST")
    print("=" * 60)
    print(f"\n📌 Topic: {topic}")
    print(f"🎨 Template: {template_id}")
    
    # Check for required API keys
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not found - cannot generate content")
        return None
    
    if not os.getenv('FAL_KEY'):
        print("⚠️  FAL_KEY not found - will generate content only, no images")
        images_enabled = False
    else:
        images_enabled = True
    
    # Step 1: Generate content
    print("\n📝 Step 1: Generating content...")
    from unified_content_generator import UnifiedContentGenerator
    
    content_gen = UnifiedContentGenerator()
    content = content_gen.generate_content(topic, num_slides=6)
    
    if not content:
        print("❌ Failed to generate content")
        return None
    
    print(f"   ✅ Generated: {content.get('title')}")
    print(f"   Type: {content.get('content_type')}")
    print(f"   Slides: {len(content.get('slides', []))}")
    
    # Save content
    safe_title = "".join(c for c in content.get('title', 'test') if c.isalnum() or c == ' ')[:30]
    safe_title = safe_title.replace(' ', '_')
    content_file = f"generated_slideshows/{safe_title}_script.json"
    os.makedirs("generated_slideshows", exist_ok=True)
    with open(content_file, 'w') as f:
        json.dump(content, f, indent=2)
    print(f"   📄 Saved script: {content_file}")
    
    # Step 2: Generate images (if enabled)
    if images_enabled:
        print("\n🎨 Step 2: Generating images...")
        from template_image_generator import TemplateImageGenerator
        
        image_gen = TemplateImageGenerator(model="gpt-image-1")
        
        image_paths = image_gen.generate_slideshow(
            template_id=template_id,
            slides=content.get('slides', []),
            title=safe_title,
            include_text=True
        )
        
        print(f"   ✅ Generated {len(image_paths)} images")
        
        content['image_paths'] = image_paths
    else:
        print("\n⏭️  Step 2: Skipped (no FAL_KEY)")
        content['image_paths'] = []
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\n📌 Title: {content.get('title')}")
    print(f"📝 Content Type: {content.get('content_type')}")
    print(f"📊 Slides: {len(content.get('slides', []))}")
    print(f"🖼️  Images: {len(content.get('image_paths', []))}")
    print(f"📄 Script: {content_file}")
    
    return content


def compare_templates(slide_text: str = "MARCUS AURELIUS"):
    """Generate the same slide with different templates for comparison"""
    
    print("\n" + "=" * 60)
    print("🔄 TEMPLATE COMPARISON")
    print("=" * 60)
    print(f"\nGenerating '{slide_text}' with each template...")
    
    if not os.getenv('FAL_KEY'):
        print("❌ FAL_KEY not found - cannot compare templates")
        return
    
    from template_image_generator import TemplateImageGenerator, TEMPLATES
    
    gen = TemplateImageGenerator(model="gpt-image-1")
    
    test_slide = {
        "display_text": slide_text,
        "slide_type": "person",
        "person_name": slide_text
    }
    
    results = []
    
    for template_id in TEMPLATES.keys():
        print(f"\n🎨 Template: {template_id}")
        
        path = gen.generate_slide(
            template_id=template_id,
            slide_data=test_slide,
            slide_number=0,
            title=f"compare_{template_id}",
            include_text=True
        )
        
        if path:
            results.append({"template": template_id, "path": path})
            print(f"   ✅ Saved: {path}")
        else:
            print(f"   ❌ Failed")
    
    print("\n" + "=" * 60)
    print(f"Generated {len(results)} template comparisons")
    print("Check the generated_slideshows folder to compare styles")
    print("=" * 60)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test unified content + template system")
    parser.add_argument('--content-only', action='store_true', help="Test content generation only")
    parser.add_argument('--image-only', action='store_true', help="Test image generation only")
    parser.add_argument('--template', type=str, help="Test specific template")
    parser.add_argument('--full', type=str, help="Full pipeline test with given topic")
    parser.add_argument('--compare', type=str, help="Compare templates with given text")
    
    args = parser.parse_args()
    
    if args.full:
        test_full_pipeline(args.full, args.template or "classical_renaissance")
    elif args.compare:
        compare_templates(args.compare)
    elif args.content_only:
        test_content_generation()
    elif args.image_only:
        test_image_templates()
    else:
        # Run all tests
        print("\n🧪 RUNNING ALL TESTS")
        print("=" * 60)
        
        # Test content generation
        test_content_generation()
        
        # Test image templates
        test_image_templates()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Review generated JSON files for content quality")
        print("  2. Review generated images in generated_slideshows/")
        print("  3. Run --compare to see template differences")
        print("  4. Run --full 'your topic' for end-to-end test")


if __name__ == "__main__":
    main()
