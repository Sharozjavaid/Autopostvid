
from google import genai
from google.genai import types
import requests
import os
from typing import List, Dict
from dotenv import load_dotenv
import base64
import json
from PIL import Image, ImageOps
import io
import re

load_dotenv()

class SmartImageGenerator:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found")
        
        self.client = genai.Client(api_key=api_key)
        self.image_model_name = 'gemini-3-pro-image-preview' # Revert to the specific image model
        self.output_dir = "generated_images"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_image_with_nano(self, prompt: str, scene_number: int, story_title: str, prompt_override: str = None) -> str:
        """Generate image using Gemini 3 Pro Image (Nano)"""
        
        # Use override if provided
        final_prompt = prompt_override if prompt_override else prompt
        
        # Optimize prompt for mobile/vertical
        if "aspect ratio" not in final_prompt.lower():
            final_prompt += ", 9:16 vertical aspect ratio, mobile wallpaper style"
        
        try:
            print(f"🎨 Calling Gemini 3 Pro Image API with Mobile Config...")
            print(f"📝 Prompt: {final_prompt[:100]}...")
            
            # Call the Gemini 3 Pro Image model
            # Note: We try to guide via prompt, but we also handle key aspect ratio in post-processing
            response = self.client.models.generate_content(
                model=self.image_model_name,
                contents=final_prompt
            )
            
            image_saved = False
            filename = ""
            
            # Helper to process parts
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        # Depending on SDK version, data might be bytes or base64 string
                        # Newer SDK usually returns bytes for inline_data.data
                        image_data = part.inline_data.data
                        
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        elif isinstance(image_data, bytes):
                            image_bytes = image_data
                        else:
                            print(f"Unknown image data type: {type(image_data)}")
                            continue
                            
                        # Convert to PIL Image
                        try:
                            image = Image.open(io.BytesIO(image_bytes))
                            
                            # SMART RESIZE: Use fit instead of resize to avoid stretching
                            # This crops the image to fill 1080x1920 instead of stretching it
                            image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
                            
                            # Save the image
                            filename = f"{self.output_dir}/{story_title.replace(' ', '_')}_scene_{scene_number}_nano.png"
                            image.save(filename, 'PNG')
                            print(f"✅ Nano image generated: {filename}")
                            image_saved = True
                            return filename
                        except Exception as img_e:
                            print(f"Error processing image bytes: {img_e}")
                            
            if not image_saved:
                # If no image in response, check for text response
                if response.text:
                    print(f"📝 Nano text response: {response.text}")
                
            # Fallback to placeholder if image generation fails
            print(f"⚠️  No image data in response, creating enhanced placeholder...")
            return self.create_enhanced_placeholder(final_prompt, scene_number, story_title)
            
        except Exception as e:
            print(f"❌ Nano image generation error: {e}")
            print(f"🔄 Falling back to enhanced placeholder...")
            return self.create_enhanced_placeholder(final_prompt, scene_number, story_title)
    
    def create_enhanced_placeholder(self, prompt: str, scene_number: int, story_title: str) -> str:
        """Create sophisticated placeholder when Nano API fails"""
        
        from PIL import ImageDraw, ImageFont
        import random
        
        # Enhanced placeholder that reflects the prompt
        width, height = 1080, 1920
        img = Image.new('RGB', (width, height), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Create sophisticated gradient based on prompt content
        if "cave" in prompt.lower() or "shadow" in prompt.lower() or "chained" in prompt.lower():
            # Dark cave aesthetic with Caravaggio-style lighting
            for y in range(height):
                darkness = int(15 + (y / height) * 50)
                golden = int((y / height) * 30) if y < height * 0.3 else 0
                draw.line([(0, y), (width, y)], fill=(darkness + golden, darkness + golden//2, darkness))
            
            # Add cave-like archway
            draw.arc([100, height//4, width-100, height//2], 0, 180, fill='#444444', width=8)
            
        elif "light" in prompt.lower() or "enlighten" in prompt.lower() or "divine" in prompt.lower():
            # Light/enlightenment aesthetic with Baroque drama
            center_x, center_y = width//2, height//3
            for radius in range(50, 500, 40):
                alpha = max(0, 120 - radius//8)
                color = (min(255, 80+alpha), min(255, 60+alpha//2), min(255, 20+alpha//4))
                draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius], 
                           outline=color, width=3)
                
        elif "philosopher" in prompt.lower() or "contemplat" in prompt.lower():
            # Classical columns and architecture
            col_width = 80
            for i in range(2):
                x = 200 + i * 600
                draw.rectangle([x, height*0.2, x+col_width, height*0.8], fill='#666666')
                # Column capital
                draw.rectangle([x-20, height*0.2, x+col_width+20, height*0.25], fill='#777777')
                
        elif "wisdom" in prompt.lower() or "temple" in prompt.lower() or "scroll" in prompt.lower():
            # Temple/library with scrolls
            draw.rectangle([width//4, height*0.4, 3*width//4, height*0.7], 
                         fill='#4a4a4a', outline='#FFD700', width=4)
            # Scroll elements
            for i in range(3):
                y_pos = height*0.5 + i*50
                draw.ellipse([width//2-30, y_pos, width//2+30, y_pos+20], fill='#D4AF37')
        
        # Add atmospheric particles
        for _ in range(25):
            x = random.randint(50, width-50)
            y = random.randint(100, height-100)
            size = random.randint(3, 12)
            alpha = random.randint(50, 150)
            draw.ellipse([x, y, x+size, y+size], fill='#FFD700')
        
        # Add title with classical styling
        try:
            title_font = ImageFont.truetype("Arial", 72)
            scene_font = ImageFont.truetype("Arial", 36)
        except:
            title_font = ImageFont.load_default()
            scene_font = ImageFont.load_default()
        
        # Extract key concept from prompt
        if "Caravaggio" in prompt:
            concept = "SHADOWS & LIGHT"
        elif "Renaissance" in prompt:
            concept = "CONTEMPLATION" 
        elif "Baroque" in prompt:
            concept = "LIBERATION"
        elif "ethereal" in prompt:
            concept = "WISDOM"
        else:
            concept = f"SCENE {scene_number}"
        
        # Add dramatic title
        bbox = draw.textbbox((0, 0), concept, font=title_font)
        text_width = bbox[2] - bbox[0]
        
        # Text shadow for depth
        shadow_x = (width - text_width) // 2 + 4
        shadow_y = height // 8 + 4
        draw.text((shadow_x, shadow_y), concept, fill='#000000', font=title_font)
        
        # Main text in gold
        main_x = (width - text_width) // 2
        main_y = height // 8
        draw.text((main_x, main_y), concept, fill='#FFD700', font=title_font)
        
        # Add "AI Generated from Prompt" watermark
        watermark = "Generated from Nano Prompt"
        draw.text((50, height-80), watermark, fill='#888888', font=scene_font)
        
        # Save enhanced placeholder
        filename = f"{self.output_dir}/{story_title.replace(' ', '_')}_scene_{scene_number}_enhanced.png"
        img.save(filename, 'PNG')
        
        print(f"🎨 Enhanced placeholder created: {filename}")
        print(f"📝 Based on prompt: {prompt[:80]}...")
        
        return filename
    
    def generate_all_images(self, story_data: Dict, scenes: List[Dict]) -> List[str]:
        """Generate all images with intelligent prompting"""
        
        print("🧠 Analyzing story for intelligent image generation...")
        
        # Get intelligent prompts from Gemini
        prompt_analysis = self.analyze_story_and_generate_image_prompts(story_data, scenes)
        
        print(f"✅ Story Analysis: {prompt_analysis.get('story_analysis', 'N/A')}")
        print(f"🎨 Visual Style: {prompt_analysis.get('overall_aesthetic', 'N/A')}")
        
        image_paths = []
        scene_prompts = prompt_analysis.get('scene_prompts', [])
        
        for i, (scene, prompt_info) in enumerate(zip(scenes, scene_prompts)):
            scene_num = i + 1
            
            image_prompt = prompt_info.get('image_prompt', 'Classical philosophical painting')
            concept = prompt_info.get('philosophical_concept', 'Wisdom')
            mood = prompt_info.get('mood', 'Contemplative')
            
            print(f"\n🎬 Scene {scene_num}: {concept}")
            print(f"🎭 Mood: {mood}")
            print(f"🖼️  Generating: {image_prompt[:80]}...")
            
            # Generate the actual image
            image_path = self.generate_image_with_nano(
                image_prompt, 
                scene_num, 
                story_data.get('title', 'Philosophy')
            )
            
            if image_path:
                image_paths.append(image_path)
        
        print(f"\n✅ Generated {len(image_paths)} intelligent images!")
        return image_paths

# Example usage
if __name__ == "__main__":
    generator = SmartImageGenerator()
    
    # Test with sample data
    story = {
        "title": "Plato's Cave Allegory",
        "script": "You sit in darkness, believing shadows are reality..."
    }
    
    scenes = [
        {"scene_number": 1, "key_concept": "Illusion", "visual_description": "Chained figures watching shadows"},
        {"scene_number": 2, "key_concept": "Questioning", "visual_description": "Philosopher contemplating reality"}
    ]
    
    images = generator.generate_all_images(story, scenes)