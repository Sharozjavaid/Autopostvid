#!/usr/bin/env python3
"""
Test script for the Slideshow Generator
Tests both the Gemini script generation and OpenAI image generation
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


def test_gemini_slideshow_script():
    """Test the Gemini slideshow script generation"""
    print("=" * 60)
    print("🧪 TEST 1: Gemini Slideshow Script Generation")
    print("=" * 60)
    
    from gemini_handler import GeminiHandler
    
    handler = GeminiHandler()
    
    test_topics = [
        "5 philosophers who changed the world",
        "3 Stoic quotes that will change your life",
    ]
    
    for topic in test_topics:
        print(f"\n📝 Generating script for: '{topic}'")
        
        script = handler.generate_slideshow_script(topic)
        
        if script:
            print(f"   ✅ Success!")
            print(f"   Title: {script.get('title', 'N/A')}")
            print(f"   Slides: {len(script.get('slides', []))}")
            
            # Show first few slides
            for slide in script.get('slides', [])[:3]:
                print(f"   - Slide {slide.get('slide_number')}: {slide.get('display_text', '')[:40]}...")
            
            # Save script for inspection
            safe_name = topic.replace(" ", "_")[:30]
            with open(f"test_slideshow_script_{safe_name}.json", "w") as f:
                json.dump(script, f, indent=2)
            print(f"   📄 Saved to: test_slideshow_script_{safe_name}.json")
        else:
            print(f"   ❌ Failed to generate script")
        
        # Only test one topic to save API calls
        break
    
    return script


def test_slideshow_generator_single_slide():
    """Test generating a single slide image"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Single Slide Generation (OpenAI)")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ⚠️ OPENAI_API_KEY not found. Skipping image generation test.")
        return None
    
    from slideshow_generator import SlideshowGenerator
    
    gen = SlideshowGenerator()
    
    # Test hook slide
    test_slide = {
        "slide_number": 0,
        "slide_type": "hook",
        "display_text": "5 PHILOSOPHERS WHO CHANGED THE WORLD",
        "subtitle": "",
        "visual_description": "Dramatic dark background with golden light rays, silhouettes of ancient philosophers in robes, epic cinematic mood, starry night sky"
    }
    
    print(f"\n🎨 Generating hook slide...")
    path = gen.generate_slide(test_slide, "Test_Slideshow")
    
    if path:
        print(f"   ✅ Success! Saved to: {path}")
    else:
        print(f"   ❌ Failed to generate slide")
    
    # Test person slide
    test_person_slide = {
        "slide_number": 1,
        "slide_type": "person",
        "person_name": "Marcus Aurelius",
        "display_text": "MARCUS AURELIUS",
        "subtitle": "Control what you can, accept what you cannot",
        "visual_description": "Roman Emperor Marcus Aurelius in imperial robes, stoic wise expression, dramatic lighting, classical painting style, Roman architecture in background"
    }
    
    print(f"\n🎨 Generating person slide...")
    path2 = gen.generate_slide(test_person_slide, "Test_Slideshow")
    
    if path2:
        print(f"   ✅ Success! Saved to: {path2}")
    else:
        print(f"   ❌ Failed to generate slide")
    
    return [path, path2]


def test_full_slideshow():
    """Test complete slideshow generation from topic"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Full Slideshow Generation (End-to-End)")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ⚠️ OPENAI_API_KEY not found. Skipping full slideshow test.")
        return None
    
    from slideshow_generator import create_slideshow
    
    topic = "3 Stoic philosophers and their most powerful ideas"
    
    print(f"\n📝 Topic: {topic}")
    print("   This will generate script with Gemini and images with OpenAI...")
    print("   (This may take 1-2 minutes)\n")
    
    result = create_slideshow(topic)
    
    if result['image_paths']:
        print(f"\n🎉 SUCCESS! Generated {len(result['image_paths'])} slides:")
        for path in result['image_paths']:
            print(f"   - {path}")
    else:
        print("\n❌ Failed to generate slideshow")
    
    return result


if __name__ == "__main__":
    print("🎴 SLIDESHOW GENERATOR TEST SUITE")
    print("=" * 60)
    
    # Check API keys
    google_key = os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"Google API Key: {'✅ Found' if google_key else '❌ Missing'}")
    print(f"OpenAI API Key: {'✅ Found' if openai_key else '❌ Missing'}")
    
    if not google_key:
        print("\n⚠️ GOOGLE_API_KEY required for script generation. Exiting.")
        exit(1)
    
    # Run tests
    try:
        # Test 1: Script generation only
        script = test_gemini_slideshow_script()
        
        if openai_key:
            # Test 2: Single slide generation
            # Uncomment to test individual slides:
            # test_slideshow_generator_single_slide()
            
            # Test 3: Full end-to-end (expensive - use sparingly)
            # Uncomment to run full test:
            # test_full_slideshow()
            
            print("\n" + "=" * 60)
            print("💡 To test image generation, uncomment the test functions above")
            print("   (Each slide costs ~$0.04-0.08 with DALL-E 3)")
            print("=" * 60)
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
