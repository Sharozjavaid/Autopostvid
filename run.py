#!/usr/bin/env python3
"""
Philosophy Video Generator - Test Runner
Quick test script to verify all components work
"""

from main import PhilosophyVideoGenerator
import asyncio

async def test_generation():
    """Test the complete video generation pipeline"""
    
    generator = PhilosophyVideoGenerator()
    
    print("🧪 Testing Philosophy Video Generator")
    print("=" * 50)
    
    # Test topic
    test_topic = "Plato's Cave Allegory"
    
    try:
        print(f"📝 Testing with topic: {test_topic}")
        
        # Generate complete video
        result = generator.generate_complete_video(test_topic)
        
        if result.get('success'):
            print("\n✅ SUCCESS! Video generation completed")
            print(f"📁 Video saved to: {result['optimized_path']}")
            print(f"🎤 Audio saved to: {result['audio_path']}")
            print(f"🎨 Images generated: {len(result['image_paths'])}")
            print(f"📚 Scenes: {len(result['story_data']['scenes'])}")
            
            # Print story preview
            story = result['story_data']
            print(f"\n📖 Generated Story Preview:")
            print(f"Hook: {story.get('hook', 'N/A')}")
            print(f"Script Length: {len(story.get('script', ''))} characters")
            print(f"App Promotion: {story.get('app_promotion', 'N/A')}")
            
        else:
            print(f"\n❌ FAILED: {result.get('error')}")
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")

if __name__ == "__main__":
    print("🚀 Starting Philosophy Video Generator Test...")
    asyncio.run(test_generation())