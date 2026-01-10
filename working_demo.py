#!/usr/bin/env python3
"""
Working Philosophy Video Demo
Creates placeholder images and demonstrates the complete pipeline
"""

import os
from PIL import Image, ImageDraw, ImageFont
import json

def create_placeholder_images():
    """Create beautiful placeholder images for the demo"""
    
    print("🎨 Creating Philosophy Video Demo")
    print("=" * 40)
    
    # Philosophy story about Plato's Cave
    scenes = [
        {
            "scene_number": 1,
            "text": "You sit in darkness, believing shadows on the wall are reality.",
            "visual_description": "Dark cave with chained figures watching shadows on wall",
            "key_concept": "Illusion",
            "duration": 7
        },
        {
            "scene_number": 2,
            "text": "But what if everything you know is just an illusion?",
            "visual_description": "Plato contemplating in classical Greek setting",
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
            "duration": 8
        }
    ]
    
    # Create output directory
    output_dir = "generated_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # TikTok dimensions
    width, height = 1080, 1920
    
    image_paths = []
    
    for scene in scenes:
        print(f"Creating image for scene {scene['scene_number']}: {scene['key_concept']}")
        
        # Create gradient background (dark to lighter)
        img = Image.new('RGB', (width, height), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Create sophisticated gradient
        for y in range(height):
            # Dark to golden gradient
            darkness = int(26 + (y / height) * 60)  
            gold_tint = int((y / height) * 40)
            color = (darkness + gold_tint, darkness + int(gold_tint * 0.8), darkness)
            draw.line([(0, y), (width, y)], fill=color)
        
        # Add mystical elements based on scene
        if scene['scene_number'] == 1:  # Cave/Shadows
            # Draw cave-like arch
            draw.ellipse([100, height//4, width-100, height//2], outline='#444444', width=5)
            # Add shadow figures
            for i in range(3):
                x = 200 + i * 250
                draw.ellipse([x, height*0.6, x+80, height*0.8], fill='#2a2a2a')
            
        elif scene['scene_number'] == 2:  # Philosophy
            # Classical columns
            for i in range(2):
                x = 200 + i * 600
                draw.rectangle([x, height*0.3, x+60, height*0.8], fill='#444444')
                draw.rectangle([x-20, height*0.3, x+80, height*0.35], fill='#555555')
            
        elif scene['scene_number'] == 3:  # Freedom/Light
            # Burst of light effect
            center_x, center_y = width//2, height//3
            for radius in range(50, 300, 50):
                draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius], 
                           outline='#FFD700', width=2)
            
        elif scene['scene_number'] == 4:  # Wisdom
            # Ancient scroll
            draw.rectangle([width//4, height//2, 3*width//4, height//2 + 200], 
                         fill='#8B7355', outline='#654321', width=3)
            # Decorative border
            draw.rectangle([width//4 + 20, height//2 + 20, 3*width//4 - 20, height//2 + 180], 
                         outline='#FFD700', width=2)
        
        # Add mystical particles/dots
        import random
        for _ in range(20):
            x = random.randint(50, width-50)
            y = random.randint(100, height-100)
            size = random.randint(2, 8)
            alpha = random.randint(100, 255)
            particle_color = f"#{alpha:02x}{alpha//2:02x}00"  # Golden particles
            draw.ellipse([x, y, x+size, y+size], fill='#FFD700')
        
        # Add scene title
        try:
            title_font = ImageFont.truetype("Arial", 80)
        except:
            title_font = ImageFont.load_default()
        
        title_text = scene['key_concept'].upper()
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        
        # Add text shadow
        shadow_x = (width - text_width) // 2 + 3
        shadow_y = height // 6 + 3
        draw.text((shadow_x, shadow_y), title_text, fill='#000000', font=title_font)
        
        # Add main text
        main_x = (width - text_width) // 2
        main_y = height // 6
        draw.text((main_x, main_y), title_text, fill='#FFD700', font=title_font)
        
        # Add scene description
        try:
            desc_font = ImageFont.truetype("Arial", 36)
        except:
            desc_font = ImageFont.load_default()
        
        # Wrap description text
        desc_lines = wrap_text(scene['visual_description'], 35)
        y_offset = height * 0.85
        
        for line in desc_lines:
            bbox = draw.textbbox((0, 0), line, font=desc_font)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, int(y_offset)), 
                     line, fill='#CCCCCC', font=desc_font)
            y_offset += 45
        
        # Add scene number
        try:
            num_font = ImageFont.truetype("Arial", 48)
        except:
            num_font = ImageFont.load_default()
        
        scene_num = f"Scene {scene['scene_number']}"
        draw.text((50, 50), scene_num, fill='#FFD700', font=num_font)
        
        # Save image
        filename = f"{output_dir}/plato_cave_scene_{scene['scene_number']}.png"
        img.save(filename, 'PNG', quality=95)
        image_paths.append(filename)
        
        print(f"  ✅ Created: {filename}")
    
    return image_paths, scenes

def wrap_text(text, width):
    """Simple text wrapping"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        if len(' '.join(current_line + [word])) <= width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def create_sample_story():
    """Create a complete story structure"""
    
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
        """.strip(),
        "hook": "You sit in darkness, believing shadows are reality...",
        "app_promotion": "Explore deeper philosophical mysteries with our app.",
        "total_duration": 30,
        "target_audience": "Philosophy learners and TikTok users"
    }
    
    return story_data

def main():
    """Main demo function"""
    
    print("🧠 Philosophy Video Generator - Working Demo")
    print("=" * 50)
    
    # Create story structure
    story = create_sample_story()
    print(f"📖 Story: {story['title']}")
    print(f"🎯 Hook: {story['hook']}")
    print(f"⏱️  Duration: {story['total_duration']} seconds")
    
    # Create images
    print(f"\n🎨 Generating Images...")
    image_paths, scenes = create_placeholder_images()
    
    # Save project data
    project_data = {
        "story": story,
        "scenes": scenes,
        "image_paths": image_paths,
        "status": "images_complete",
        "next_steps": [
            "Add ElevenLabs API key for voice generation",
            "Install MoviePy for video assembly", 
            "Generate final TikTok video"
        ]
    }
    
    with open("demo_project.json", "w") as f:
        json.dump(project_data, f, indent=2)
    
    print(f"\n✅ Demo Complete!")
    print(f"📁 Created {len(image_paths)} philosophical images")
    print(f"💾 Project saved to: demo_project.json")
    print(f"\n🖼️  View your images in: generated_images/")
    
    print(f"\n📱 Next Steps:")
    print(f"   1. Check the beautiful philosophical images created")
    print(f"   2. Add valid API keys for full video generation")
    print(f"   3. Run the complete pipeline for TikTok videos")
    
    print(f"\n🎬 This demonstrates the complete video structure:")
    print(f"   ✅ Story generation (Plato's Cave)")
    print(f"   ✅ Scene breakdown (4 scenes)")  
    print(f"   ✅ Classical image creation")
    print(f"   🔄 Voice generation (needs API key)")
    print(f"   🔄 Video assembly (needs MoviePy)")
    
    return project_data

if __name__ == "__main__":
    result = main()