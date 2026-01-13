#!/usr/bin/env python3
"""
OpenAI Image Generator for Philosophy Videos
Alternative to Gemini/Nano - can be used in Streamlit app
"""

import os
from dotenv import load_dotenv
from PIL import Image, ImageOps
import io
import requests
import base64
from typing import List, Optional

load_dotenv()

# Model options
OPENAI_MODELS = {
    "dall-e-3": {
        "size": "1024x1792",
        "quality": "hd",
        "max_n": 1  # DALL-E 3 only supports n=1
    },
    "gpt-image-1.5": {
        "size": "1024x1536",
        "quality": "high",
        "max_n": 4  # gpt-image-1.5 supports multiple images
    }
}

DEFAULT_MODEL = "dall-e-3"  # Use DALL-E 3 by default (no verification needed)


class OpenAIImageGenerator:
    def __init__(self, model: str = None):
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            self.client = OpenAI(api_key=api_key)
            self.model = model or DEFAULT_MODEL
            self.output_dir = "generated_images"
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Get model config
            self.model_config = OPENAI_MODELS.get(self.model, OPENAI_MODELS[DEFAULT_MODEL])
            print(f"✅ OpenAI Image Generator initialized with model: {self.model}")
            
        except ImportError:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Error initializing OpenAI client: {e}")
    
    def generate_image(self, prompt: str, scene_number: int, story_title: str, n: int = 1) -> List[str]:
        """
        Generate image(s) using OpenAI's image generation.
        
        Args:
            prompt: The image generation prompt
            scene_number: Scene number for filename
            story_title: Story title for filename
            n: Number of images to generate (only gpt-image-1.5 supports n>1)
        
        Returns:
            List of saved image paths
        """
        
        # Optimize prompt for mobile/vertical
        if "aspect ratio" not in prompt.lower():
            prompt += ", 9:16 vertical aspect ratio, mobile wallpaper style"
        
        # Limit n based on model
        max_n = self.model_config.get("max_n", 1)
        n = min(n, max_n)
        
        try:
            print(f"🎨 Calling OpenAI {self.model} for image generation (n={n})...")
            print(f"📝 Prompt: {prompt[:100]}...")
            
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                n=n,
                size=self.model_config["size"],
                quality=self.model_config["quality"]
            )
            
            saved_paths = []
            
            for idx, image_data in enumerate(response.data):
                # Download from URL
                if image_data.url:
                    img_response = requests.get(image_data.url)
                    image_bytes = img_response.content
                elif hasattr(image_data, 'b64_json') and image_data.b64_json:
                    image_bytes = base64.b64decode(image_data.b64_json)
                else:
                    print(f"⚠️ No image data for index {idx}")
                    continue
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Resize to exact TikTok dimensions using smart fit
                image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
                
                # Save the image
                suffix = f"_v{idx+1}" if n > 1 else ""
                filename = f"{self.output_dir}/{story_title.replace(' ', '_')}_scene_{scene_number}_openai{suffix}.png"
                image.save(filename, 'PNG')
                saved_paths.append(filename)
                print(f"✅ Image saved: {filename}")
            
            return saved_paths
                
        except Exception as e:
            print(f"❌ OpenAI image generation error: {e}")
            return []
    
    def generate_philosophy_image(self, scene_data: dict, story_title: str, n: int = 1) -> List[str]:
        """Generate classical philosophy images for a scene"""
        
        visual_desc = scene_data.get('visual_description', '')
        scene_text = scene_data.get('text', '')
        key_concept = scene_data.get('key_concept', '')
        scene_num = scene_data.get('scene_number', 1)
        
        prompt = f"""A haunting classical painting in the style of Caravaggio or Rembrandt.

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

The image should evoke wonder, introspection, and the pursuit of wisdom.
Make it visually striking enough to stop scrollers on TikTok."""
        
        return self.generate_image(prompt, scene_num, story_title, n=n)
    
    def generate_batch(self, scenes: List[dict], story_title: str, global_style: str = None) -> List[str]:
        """Generate images for all scenes"""
        
        all_paths = []
        
        for scene in scenes:
            scene_num = scene.get('scene_number', 1)
            
            if global_style:
                visual_desc = scene.get('visual_description', '')
                key_concept = scene.get('key_concept', '')
                prompt = f"{global_style}, {visual_desc}, {key_concept}"
                paths = self.generate_image(prompt, scene_num, story_title)
            else:
                paths = self.generate_philosophy_image(scene, story_title)
            
            if paths:
                all_paths.extend(paths)
        
        print(f"✅ Generated {len(all_paths)} images for {len(scenes)} scenes")
        return all_paths


def check_openai_available() -> bool:
    """Check if OpenAI is available and configured"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return False
        from openai import OpenAI
        return True
    except ImportError:
        return False
