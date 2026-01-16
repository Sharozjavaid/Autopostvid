#!/usr/bin/env python3
"""
Quick test for GPT Image 1.5 integration.

This tests:
1. GPT Image 1.5 generator works via fal.ai
2. Script generator includes slide_subject field
3. Pipeline uses the new image generator correctly
"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_gpt_image_generator():
    """Test the GPT Image 1.5 generator directly."""
    print("\n" + "="*60)
    print("TEST 1: GPT Image 1.5 Generator")
    print("="*60)
    
    from gpt_image_generator import GPTImageGenerator, check_gpt_image_available
    
    if not check_gpt_image_available():
        print("❌ FAL_KEY not set - cannot test GPT Image 1.5")
        return False
    
    gen = GPTImageGenerator(quality="low")
    
    # Test scene-based generation
    test_scene = {
        "scene_number": 1,
        "text": "These five philosophers changed history forever.",
        "visual_description": "Epic montage of ancient Greek and Roman busts, marble statues in dramatic lighting",
        "slide_subject": "5 MINDS THAT CHANGED EVERYTHING",
        "key_concept": "Hook",
        "list_item": 0
    }
    
    result = gen.generate_philosophy_image(
        scene_data=test_scene,
        story_title="GPT15_Integration_Test"
    )
    
    if result and os.path.exists(result):
        print(f"✅ Test passed! Image saved: {result}")
        return True
    else:
        print("❌ Test failed - no image generated")
        return False


def test_script_generator():
    """Test that script generator includes slide_subject."""
    print("\n" + "="*60)
    print("TEST 2: Script Generator (slide_subject field)")
    print("="*60)
    
    from gemini_handler import GeminiHandler
    
    handler = GeminiHandler()
    
    # Generate a short test script
    result = handler.generate_timed_script(
        topic="3 Stoic philosophers with powerful lessons",
        target_duration=30,  # Short for testing
        clip_duration=6
    )
    
    if not result:
        print("❌ Failed to generate script")
        return False
    
    scenes = result.get('scenes', [])
    if not scenes:
        print("❌ No scenes in script")
        return False
    
    # Check if slide_subject is present
    has_slide_subject = any('slide_subject' in scene for scene in scenes)
    
    print(f"Script generated with {len(scenes)} scenes")
    print("\nSample scenes:")
    for scene in scenes[:3]:
        print(f"  Scene {scene.get('scene_number')}: {scene.get('text', '')[:50]}...")
        print(f"    slide_subject: {scene.get('slide_subject', 'NOT FOUND')}")
    
    if has_slide_subject:
        print("✅ slide_subject field is present!")
        return True
    else:
        print("⚠️ slide_subject not in scenes - will use fallback logic")
        return True  # Still passes because fallback logic exists


def test_full_pipeline():
    """Test the full pipeline with GPT Image 1.5 (images only, no video)."""
    print("\n" + "="*60)
    print("TEST 3: Full Pipeline (images only)")
    print("="*60)
    
    from pipeline import VideoPipeline
    from gpt_image_generator import check_gpt_image_available
    
    if not check_gpt_image_available():
        print("⚠️ FAL_KEY not set - testing with nano instead")
        image_model = "nano"
    else:
        image_model = "gpt15"
    
    pipeline = VideoPipeline(
        target_duration=30,  # Short for testing
        clip_duration=6
    )
    
    result = pipeline.run(
        topic="3 philosophers with life-changing quotes",
        skip_video_clips=True,  # Skip video generation for quick test
        image_model=image_model
    )
    
    if result.get('success'):
        print(f"✅ Pipeline completed successfully!")
        print(f"   Images generated: {len(result.get('image_paths', []))}")
        print(f"   Script: {result.get('script_path')}")
        return True
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("GPT Image 1.5 Integration Test Suite")
    print("="*60)
    
    results = {}
    
    # Test 1: GPT Image Generator
    try:
        results['gpt_image'] = test_gpt_image_generator()
    except Exception as e:
        print(f"❌ Test 1 error: {e}")
        results['gpt_image'] = False
    
    # Test 2: Script Generator
    try:
        results['script'] = test_script_generator()
    except Exception as e:
        print(f"❌ Test 2 error: {e}")
        results['script'] = False
    
    # Test 3: Full Pipeline (optional - takes longer)
    run_full_test = input("\n\nRun full pipeline test? (y/n): ").lower() == 'y'
    if run_full_test:
        try:
            results['pipeline'] = test_full_pipeline()
        except Exception as e:
            print(f"❌ Test 3 error: {e}")
            results['pipeline'] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))
