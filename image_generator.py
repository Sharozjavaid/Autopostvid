import google.generativeai as genai
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class ImageGenerator:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-3-pro-image-preview')
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_philosophy_image(self, scene_data: Dict, story_title: str) -> str:
        """Generate a classical, dark, mysterious image for philosophy story scene"""
        
        visual_desc = scene_data.get('visual_description', '')
        scene_text = scene_data.get('text', '')
        key_concept = scene_data.get('key_concept', '')
        
        prompt = f"""
        Create a stunning philosophical image in classical painting style.
        
        Story: {story_title}
        Scene Context: {scene_text}
        Visual Description: {visual_desc}
        Key Concept: {key_concept}
        
        Style Requirements:
        - Classical Renaissance/Baroque painting aesthetic
        - Dark, moody atmosphere with dramatic chiaroscuro lighting
        - Rich, deep colors: golds, deep blues, burgundy, dark browns
        - Mysterious shadows with strategic golden highlights
        - Philosophical symbolism and metaphorical elements
        - Vertical composition optimized for 9:16 TikTok format
        - Contemplative, introspective mood
        - Ancient or timeless setting elements
        
        Visual Elements to Include:
        - Dramatic lighting that creates depth and mystery
        - Classical architectural elements if relevant
        - Symbolic objects (scrolls, books, candles, mirrors)
        - Figures in contemplative poses
        - Atmospheric effects (mist, soft glows, shadows)
        
        The image should evoke wonder, introspection, and the pursuit of wisdom.
        Make it visually striking enough to stop scrollers on TikTok.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Note: Since actual image generation APIs vary, this is a placeholder
            # In practice, you'd integrate with the actual Gemini image generation API
            # For now, we'll create a text-based response and handle image generation separately
            
            scene_num = scene_data.get('scene_number', 1)
            filename = f"{self.output_dir}/scene_{scene_num}_{story_title.replace(' ', '_')}.png"
            
            # Placeholder for actual image generation
            # This would be replaced with actual API call to generate image
            self.create_placeholder_image(filename, visual_desc, scene_num)
            
            return filename
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def create_placeholder_image(self, filename: str, description: str, scene_num: int):
        """Create a placeholder image with scene description (for testing)"""
        
        # Create a dark, classical-looking placeholder
        width, height = 1080, 1920  # TikTok vertical format
        
        # Create gradient background
        img = Image.new('RGB', (width, height), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Create gradient effect
        for y in range(height):
            darkness = int(26 + (y / height) * 40)  # Gradient from dark to slightly lighter
            color = f"#{darkness:02x}{darkness:02x}{darkness:02x}"
            draw.line([(0, y), (width, y)], fill=color)
        
        # Add golden highlights
        draw.ellipse([width//4, height//3, 3*width//4, 2*height//3], 
                    outline='#FFD700', width=3)
        
        # Add scene number
        try:
            font = ImageFont.truetype("Arial", 60)
        except:
            font = ImageFont.load_default()
        
        scene_text = f"Scene {scene_num}"
        bbox = draw.textbbox((0, 0), scene_text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) // 2, height // 6), 
                 scene_text, fill='#FFD700', font=font)
        
        # Add description (wrapped)
        desc_lines = self.wrap_text(description, 40)
        try:
            desc_font = ImageFont.truetype("Arial", 24)
        except:
            desc_font = ImageFont.load_default()
        
        y_offset = height // 2
        for line in desc_lines:
            bbox = draw.textbbox((0, 0), line, font=desc_font)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, y_offset), 
                     line, fill='#E6E6E6', font=desc_font)
            y_offset += 40
        
        img.save(filename)
    
    def wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width"""
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
    
    def generate_all_scene_images(self, scenes: List[Dict], story_title: str) -> List[str]:
        """Generate images for all scenes in the story"""
        image_paths = []
        
        for scene in scenes:
            print(f"Generating image for scene {scene.get('scene_number', '?')}...")
            image_path = self.generate_philosophy_image(scene, story_title)
            if image_path:
                image_paths.append(image_path)
            
        return image_paths

# Example usage
if __name__ == "__main__":
    # Test image generation
    test_scene = {
        'scene_number': 1,
        'text': 'You are chained in darkness, seeing only shadows on the wall.',
        'visual_description': 'Dark cave with figures chained, watching shadows on stone wall',
        'key_concept': 'illusion of reality'
    }
    
    generator = ImageGenerator()
    image_path = generator.generate_philosophy_image(test_scene, "Platos_Cave")
    print(f"Generated image: {image_path}")