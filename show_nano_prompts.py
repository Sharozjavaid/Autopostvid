#!/usr/bin/env python3
"""
Show the exact prompts that would be sent to Nano image generation
"""

def show_nano_prompting_system():
    """Demonstrate the intelligent prompting system for Nano"""
    
    print("🎨 NANO IMAGE GENERATION - INTELLIGENT PROMPTING SYSTEM")
    print("=" * 70)
    
    # Sample story data (what Gemini would generate)
    story_data = {
        "title": "Plato's Cave Allegory", 
        "script": """
        You sit in darkness, believing shadows on the wall are reality.
        These dancing forms seem so real, so meaningful.
        But what if everything you know is just an illusion?
        This profound question drives Plato's famous Cave Allegory.
        Imagine being freed from these chains of ignorance.
        What would you see when you step into the light?
        True knowledge awaits those brave enough to question reality.
        Explore deeper philosophical mysteries with our app.
        """,
        "hook": "You sit in darkness, believing shadows are reality...",
        "app_promotion": "Explore deeper philosophical mysteries with our app."
    }
    
    scenes = [
        {
            "scene_number": 1,
            "text": "You sit in darkness, believing shadows on the wall are reality.",
            "visual_description": "Dark cave with chained figures watching shadows",
            "key_concept": "Illusion",
            "duration": 8
        },
        {
            "scene_number": 2,
            "text": "But what if everything you know is just an illusion?",
            "visual_description": "Plato contemplating reality in classical setting",
            "key_concept": "Questioning", 
            "duration": 7
        },
        {
            "scene_number": 3,
            "text": "Imagine being freed from these chains of ignorance.",
            "visual_description": "Figure breaking free into bright light",
            "key_concept": "Freedom",
            "duration": 8
        },
        {
            "scene_number": 4,
            "text": "True knowledge awaits those brave enough to question reality.",
            "visual_description": "Wise figure with scroll in temple of wisdom",
            "key_concept": "Wisdom",
            "duration": 7
        }
    ]
    
    print("📖 STORY CONTEXT:")
    print(f"Title: {story_data['title']}")
    print(f"Script: {story_data['script'][:100]}...")
    print(f"Scenes: {len(scenes)}")
    
    print("\n🧠 WHAT GEMINI WOULD ANALYZE AND SEND TO NANO:")
    print("=" * 50)
    
    # This is what the intelligent system would generate
    intelligent_analysis = {
        "story_analysis": "A philosophical allegory about the nature of reality, truth, and enlightenment. The narrative follows a journey from ignorance to knowledge, from shadow to light.",
        "overall_aesthetic": "Classical Renaissance painting style with dramatic chiaroscuro lighting. Dark, mysterious atmosphere with philosophical symbolism. Vertical composition for TikTok format.",
        "scene_prompts": [
            {
                "scene_number": 1,
                "philosophical_concept": "The Illusion of Reality",
                "image_prompt": "A haunting classical painting in the style of Caravaggio, showing silhouetted figures chained in a dark stone cave, their faces illuminated by flickering firelight as they stare at dancing shadows on the rough wall. The composition should be vertical (9:16), with dramatic chiaroscuro lighting creating deep shadows and golden highlights. The shadows on the wall should appear almost alive, suggesting movement and false reality. Rich color palette of deep browns, amber firelight, and mysterious blacks. The scene should evoke a sense of captivity and unknowing, with the chained figures representing humanity's bondage to illusion.",
                "visual_metaphor": "Chains represent mental bondage to false beliefs",
                "mood": "Dark, mysterious, contemplative",
                "color_palette": "Deep browns, amber, charcoal, flickering gold"
            },
            {
                "scene_number": 2, 
                "philosophical_concept": "Philosophical Questioning",
                "image_prompt": "A magnificent Renaissance-style portrait of an ancient Greek philosopher (representing Plato) in contemplative pose, surrounded by classical marble columns and scrolls. The figure should be depicted in profile, with one hand touching his bearded chin in thought, eyes gazing upward toward divine light streaming through classical architecture. The lighting should be reminiscent of Rembrandt's style - dramatic side lighting casting thoughtful shadows. Vertical composition optimized for TikTok. Color palette of rich blues, golden light, marble whites, and deep shadows. Ancient Greek architectural elements in the background should suggest timeless wisdom.",
                "visual_metaphor": "The philosopher represents the questioning mind seeking truth",
                "mood": "Intellectual, contemplative, noble",
                "color_palette": "Royal blues, golden light, marble white, bronze"
            },
            {
                "scene_number": 3,
                "philosophical_concept": "Liberation and Enlightenment", 
                "image_prompt": "A dramatic painting in the style of Baroque masters, showing a human figure breaking free from heavy iron chains, emerging from darkness into brilliant divine light. The figure should be captured mid-motion, one foot still in shadow, one reaching toward a golden sunrise. Broken chains should be falling away dramatically. The light source should be overwhelming and ethereal, suggesting transcendence. Vertical composition with the figure positioned in the center, rising upward. The contrast between the dark cave below and radiant light above should be stark and emotional. Color palette emphasizing the transition from darkness to light - deep charcoals transitioning to brilliant golds and whites.",
                "visual_metaphor": "Breaking chains represents freedom from ignorance",
                "mood": "Triumphant, liberating, transformative",
                "color_palette": "Dark grays transitioning to brilliant gold, white light"
            },
            {
                "scene_number": 4,
                "philosophical_concept": "Wisdom and True Knowledge",
                "image_prompt": "An ethereal classical painting depicting a wise sage in flowing robes, standing in an ancient temple or library filled with scrolls and books. The figure should be holding an unrolled scroll containing mysterious symbols or text, bathed in soft, divine light filtering through tall windows. Ancient Greek or Roman architectural elements should frame the scene. The atmosphere should suggest reverence for knowledge and learning. Vertical composition with the wise figure positioned prominently in the center. Soft, warm lighting should create a sense of peace and enlightenment. Color palette of warm golds, sage greens, marble whites, and soft shadows.",
                "visual_metaphor": "The scroll represents accumulated wisdom and truth",
                "mood": "Serene, wise, enlightened",
                "color_palette": "Warm golds, sage green, ivory, soft shadows"
            }
        ]
    }
    
    print("🎭 SCENE-BY-SCENE NANO PROMPTS:")
    print("-" * 50)
    
    for prompt_info in intelligent_analysis["scene_prompts"]:
        print(f"\n🎬 SCENE {prompt_info['scene_number']}: {prompt_info['philosophical_concept'].upper()}")
        print(f"🎭 Mood: {prompt_info['mood']}")
        print(f"🎨 Colors: {prompt_info['color_palette']}")
        print(f"💭 Metaphor: {prompt_info['visual_metaphor']}")
        print(f"\n🖼️  NANO PROMPT:")
        print(f"   {prompt_info['image_prompt']}")
        print("-" * 50)
    
    print(f"\n🎯 KEY IMPROVEMENTS IN THIS SYSTEM:")
    print(f"✅ Gemini analyzes the FULL story context, not just individual scenes")
    print(f"✅ Each prompt is tailored to the specific philosophical concept")
    print(f"✅ References classical painting masters (Caravaggio, Rembrandt, Baroque)")
    print(f"✅ Optimized for TikTok vertical format (9:16)")
    print(f"✅ Detailed lighting and composition instructions")
    print(f"✅ Rich color palettes that match the emotional tone")
    print(f"✅ Visual metaphors that reinforce the philosophical message")
    print(f"✅ Cinematic quality descriptions for high-quality output")
    
    print(f"\n🔧 TO CONNECT TO NANO:")
    print(f"1. Replace the placeholder generation in smart_image_generator.py")
    print(f"2. Add your Nano API endpoint and key")
    print(f"3. Send these detailed prompts to Nano")
    print(f"4. The result will be stunning classical philosophy images!")
    
    return intelligent_analysis

if __name__ == "__main__":
    analysis = show_nano_prompting_system()
    print(f"\n🎉 This shows exactly what prompts Nano would receive!")
    print(f"💡 Much more sophisticated than generic prompts!")