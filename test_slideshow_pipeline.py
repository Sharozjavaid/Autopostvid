#!/usr/bin/env python3
"""
Test script for the slideshow pipeline.

This runs a comparison test between Flux and GPT15 on the same topic
to verify the pipeline works before deploying to GCP.

Usage:
    python test_slideshow_pipeline.py
    python test_slideshow_pipeline.py --topic "Your custom topic"
"""

import os
import sys
import argparse

# Test topic
DEFAULT_TOPIC = "Occam's Razor: The Power of Simplicity"


def test_single_model(topic: str, model: str = "flux"):
    """Test a single model."""
    from slideshow_automation import generate_slideshow
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing {model.upper()} on: {topic}")
    print(f"{'='*60}\n")
    
    result = generate_slideshow(
        topic=topic,
        model=model,
        font_name="social",  # Use social font
        visual_style="modern",
        auto_id=f"TEST_{model.upper()}"
    )
    
    if result.get("success"):
        print(f"\n✅ {model.upper()} SUCCESS!")
        print(f"   Slides: {result.get('slides_count')}")
        print(f"   Output: {result.get('output_dir')}")
        print(f"\n   Files:")
        for path in result.get("image_paths", []):
            print(f"      {path}")
    else:
        print(f"\n❌ {model.upper()} FAILED: {result.get('error')}")
    
    return result


def test_comparison(topic: str):
    """Compare both models on the same topic."""
    from slideshow_automation import compare_models
    
    print(f"\n{'='*60}")
    print(f"🔬 COMPARISON TEST")
    print(f"   Topic: {topic}")
    print(f"   Font: social")
    print(f"{'='*60}\n")
    
    results = compare_models(topic, font_name="social")
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    
    for model, result in results.items():
        status = "✅" if result.get("success") else "❌"
        slides = result.get("slides_count", 0)
        print(f"\n{status} {model.upper()}:")
        print(f"   Slides: {slides}")
        
        if result.get("success"):
            print(f"   Output directory: {result.get('output_dir')}")
            print(f"   First slide: {result.get('image_paths', ['N/A'])[0]}")
    
    return results


def test_automation_manager():
    """Test the automation manager with the new fields."""
    from automation_manager import AutomationManager, AUTOMATION_TYPES, IMAGE_MODELS, FONT_STYLES
    
    print(f"\n{'='*60}")
    print(f"🔧 AUTOMATION MANAGER TEST")
    print(f"{'='*60}\n")
    
    print("📋 Available Automation Types:")
    for key, info in AUTOMATION_TYPES.items():
        print(f"   {info['icon']} {key}: {info['name']}")
        print(f"      {info['description']}")
    
    print("\n🎨 Available Image Models:")
    for key, info in IMAGE_MODELS.items():
        paused = " (PAUSED)" if info.get("paused") else ""
        print(f"   {info['icon']} {key}: {info['name']}{paused}")
        print(f"      {info['description']} [{info['cost']}]")
    
    print("\n📝 Available Font Styles:")
    for key, info in FONT_STYLES.items():
        default = " (DEFAULT)" if info.get("default") else ""
        print(f"   {key}: {info['name']}{default}")
    
    # Test creating an automation
    print("\n🧪 Creating test automation...")
    manager = AutomationManager()
    
    auto = manager.create_automation(
        name="Test Slideshow - Flux",
        description="Test slideshow automation with Flux model",
        automation_type="slideshow",
        image_model="flux",
        font_name="social",
        visual_style="modern",
        schedule_mode="single",
        topics=["Test topic 1", "Test topic 2"]
    )
    
    print(f"   ✅ Created automation: {auto.id}")
    print(f"      Name: {auto.name}")
    print(f"      Type: {auto.automation_type}")
    print(f"      Model: {auto.image_model}")
    print(f"      Font: {auto.font_name}")
    
    # Get stats
    stats = manager.get_stats_summary()
    print(f"\n📊 Stats Summary:")
    print(f"   Total automations: {stats['total_automations']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   By model: {stats['by_model']}")
    
    # Clean up test automation
    manager.delete_automation(auto.id)
    print(f"\n   🗑️ Deleted test automation")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Test the slideshow pipeline")
    
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default=DEFAULT_TOPIC,
        help=f"Topic to test (default: {DEFAULT_TOPIC})"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        choices=["flux", "gpt15", "both"],
        default="both",
        help="Which model to test (default: both)"
    )
    
    parser.add_argument(
        "--manager-only",
        action="store_true",
        help="Only test the automation manager (no image generation)"
    )
    
    args = parser.parse_args()
    
    print("🧪 SLIDESHOW PIPELINE TEST")
    print("=" * 60)
    print(f"Topic: {args.topic}")
    print(f"Model: {args.model}")
    print("=" * 60)
    
    # Test automation manager first (quick, no API calls)
    test_automation_manager()
    
    if args.manager_only:
        print("\n✅ Manager test complete!")
        return
    
    # Test image generation
    if args.model == "both":
        results = test_comparison(args.topic)
    elif args.model == "flux":
        test_single_model(args.topic, "flux")
    elif args.model == "gpt15":
        test_single_model(args.topic, "gpt15")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)
    print("\nCheck the generated_slideshows/ directory for output files.")


if __name__ == "__main__":
    main()
