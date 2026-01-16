#!/usr/bin/env python3
"""
Test the new Philosophical Mentor-style Slideshow Generator

This tests the generate_mentor_slideshow() method which creates scripts
in a direct, no-nonsense motivational tone with the specific structure:
- Slide 1: Hook (1 text item, 6-10 words)
- Slides 2-6: Three-part structure (insight + "What it does" + "Why it matters")
- Slide 7: Outro (rhetorical question + call to action + philosophical truth)
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


def test_mentor_slideshow():
    """Test the philosophical mentor-style slideshow generation"""
    print("=" * 70)
    print("🧪 TESTING PHILOSOPHICAL MENTOR SLIDESHOW GENERATOR")
    print("=" * 70)
    
    from gemini_handler import GeminiHandler
    
    handler = GeminiHandler()
    
    # Test topics that work well with the mentor style
    test_topics = [
        "Why you can't think clearly",
        "The truth about your overthinking",
        "5 mental traps keeping you stuck",
        "Why chasing happiness makes you miserable",
        "The philosophy of letting go"
    ]
    
    print("\n📋 Available test topics:")
    for i, topic in enumerate(test_topics, 1):
        print(f"   {i}. {topic}")
    
    # Test with the first topic
    selected_topic = test_topics[0]
    print(f"\n📝 Generating mentor-style slideshow for: '{selected_topic}'")
    print("   (This uses the new generate_mentor_slideshow() method)")
    print()
    
    try:
        script = handler.generate_mentor_slideshow(selected_topic)
        
        if script:
            print(f"   ✅ Success!")
            print()
            print("=" * 70)
            print("📊 SCRIPT STRUCTURE")
            print("=" * 70)
            print(f"   Title: {script.get('title', 'N/A')}")
            print(f"   Content Type: {script.get('content_type', 'N/A')}")
            print(f"   Writing Style: {script.get('writing_style', 'N/A')}")
            print(f"   Total Slides: {script.get('total_slides', 0)}")
            print()
            
            slides = script.get('slides', [])
            
            print("=" * 70)
            print("📄 SLIDE BREAKDOWN")
            print("=" * 70)
            
            for slide in slides:
                slide_num = slide.get('slide_number', '?')
                slide_type = slide.get('slide_type', '?')
                text_items = slide.get('text_items', [])
                
                print(f"\n🔹 SLIDE {slide_num} ({slide_type.upper()})")
                print("-" * 70)
                
                for i, item in enumerate(text_items, 1):
                    label = item.get('label', '')
                    text = item.get('text', '')
                    font_size = item.get('font_size', 'unknown')
                    word_count = item.get('word_count', 0)
                    
                    if label:
                        print(f"   {i}. [{font_size}] {label} {text}")
                    else:
                        print(f"   {i}. [{font_size}] {text}")
                    print(f"      └─ Word count: {word_count}")
                
                visual = slide.get('visual_description', '')
                if visual:
                    print(f"\n   🎨 Visual: {visual[:80]}...")
            
            # Validate structure
            print()
            print("=" * 70)
            print("✅ VALIDATION")
            print("=" * 70)
            
            errors = []
            
            # Check total slides
            if len(slides) != 7:
                errors.append(f"❌ Expected 7 slides, got {len(slides)}")
            else:
                print("   ✓ Correct number of slides (7)")
            
            # Check slide 1 (hook)
            if slides and slides[0].get('slide_type') == 'hook':
                hook_items = slides[0].get('text_items', [])
                if len(hook_items) != 1:
                    errors.append(f"❌ Slide 1 should have 1 text item, has {len(hook_items)}")
                else:
                    print("   ✓ Slide 1 has correct structure (1 text item)")
                    hook_words = hook_items[0].get('word_count', 0)
                    if not (6 <= hook_words <= 10):
                        errors.append(f"⚠️  Hook word count ({hook_words}) outside 6-10 range")
            
            # Check slides 2-6 (content)
            for i in range(1, 6):
                if i < len(slides):
                    slide = slides[i]
                    if slide.get('slide_type') == 'content':
                        items = slide.get('text_items', [])
                        if len(items) != 3:
                            errors.append(f"❌ Slide {i+1} should have 3 text items, has {len(items)}")
                        else:
                            # Check for required labels
                            labels = [item.get('label', '') for item in items]
                            if 'What it does:' not in labels:
                                errors.append(f"⚠️  Slide {i+1} missing 'What it does:' label")
                            if 'Why it matters:' not in labels:
                                errors.append(f"⚠️  Slide {i+1} missing 'Why it matters:' label")
            
            if not errors:
                print("   ✓ Content slides have correct structure (3 text items each)")
            
            # Check slide 7 (outro)
            if len(slides) >= 7:
                outro = slides[6]
                outro_items = outro.get('text_items', [])
                if len(outro_items) < 2 or len(outro_items) > 3:
                    errors.append(f"❌ Slide 7 should have 2-3 text items, has {len(outro_items)}")
                else:
                    print("   ✓ Slide 7 has correct structure (2-3 text items)")
            
            if errors:
                print()
                print("⚠️  VALIDATION WARNINGS:")
                for error in errors:
                    print(f"   {error}")
            else:
                print()
                print("🎉 ALL VALIDATIONS PASSED!")
            
            # Save script for inspection
            safe_name = selected_topic.replace(" ", "_").replace("'", "")[:40]
            output_file = f"test_mentor_script_{safe_name}.json"
            with open(output_file, "w") as f:
                json.dump(script, f, indent=2)
            
            print()
            print("=" * 70)
            print(f"📄 Full script saved to: {output_file}")
            print("=" * 70)
            
            return script
        else:
            print(f"   ❌ Failed to generate script")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def show_usage_example():
    """Show how to use this in other scripts"""
    print()
    print("=" * 70)
    print("💡 HOW TO USE IN YOUR CODE")
    print("=" * 70)
    print("""
from gemini_handler import GeminiHandler

# Initialize handler
handler = GeminiHandler()

# Generate mentor-style slideshow
topic = "Why you can't think clearly"
script = handler.generate_mentor_slideshow(topic)

# Access the data
if script:
    for slide in script['slides']:
        slide_num = slide['slide_number']
        slide_type = slide['slide_type']
        text_items = slide['text_items']
        visual = slide['visual_description']
        
        # Process each text item
        for item in text_items:
            text = item['text']
            font_size = item['font_size']  # 'large', 'medium', 'medium-large', 'small'
            label = item.get('label', '')   # 'What it does:' or 'Why it matters:'
            
            # Generate your slide image here...
    """)


if __name__ == "__main__":
    print("🎴 PHILOSOPHICAL MENTOR SLIDESHOW TEST")
    print()
    
    # Check API key
    google_key = os.getenv('GOOGLE_API_KEY')
    
    if not google_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("   Please add it to your .env file")
        exit(1)
    
    print(f"✅ Google API Key found")
    
    # Run test
    try:
        script = test_mentor_slideshow()
        
        if script:
            show_usage_example()
            print()
            print("✅ Test completed successfully!")
        else:
            print("\n❌ Test failed")
            exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
