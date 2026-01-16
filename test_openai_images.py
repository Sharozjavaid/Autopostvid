#!/usr/bin/env python3
"""
Test image generation using OpenAI's gpt-image-1.5 model
Alternative to Gemini/Nano for philosophy video images
"""

import os
from dotenv import load_dotenv
from PIL import Image, ImageOps
import io
import requests
import base64

load_dotenv()

# OpenAI image generation model
# Options: "gpt-image-1.5" (requires org verification) or "dall-e-3" (no verification needed)
OPENAI_IMAGE_MODEL = "dall-e-3"  # Using DALL-E 3 as fallback since gpt-image-1.5 requires verification

class OpenAIImageGenerator:
    def __init__(self, model: str = None):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = model or OPENAI_IMAGE_MODEL
            self.output_dir = "generated_images"
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"✅ OpenAI client initialized with model: {self.model}")
        except ImportError:
            print("❌ OpenAI SDK not installed. Run: pip install openai")
            raise
        except Exception as e:
            print(f"❌ Error initializing OpenAI client: {e}")
            raise
    
    def generate_image(self, prompt: str, scene_number: int, story_title: str) -> str:
        """Generate image using OpenAI's image generation"""
        
        # Optimize prompt for mobile/vertical
        if "aspect ratio" not in prompt.lower():
            prompt += ", 9:16 vertical aspect ratio, mobile wallpaper style"
        
        try:
            print(f"🎨 Calling OpenAI {self.model} for image generation...")
            print(f"📝 Prompt: {prompt[:100]}...")
            
            # Use the images.generate endpoint
            # Different sizes for different models
            if self.model == "dall-e-3":
                size = "1024x1792"  # DALL-E 3 vertical format
                quality_param = "hd"
            else:
                size = "1024x1536"  # gpt-image-1.5 vertical format
                quality_param = "high"
            
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                n=1,
                size=size,
                quality=quality_param
            )
            
            if response.data and len(response.data) > 0:
                # gpt-image-1.5 returns URL by default
                image_url = response.data[0].url
                if image_url:
                    # Download the image
                    img_response = requests.get(image_url)
                    image_bytes = img_response.content
                elif hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                    image_bytes = base64.b64decode(response.data[0].b64_json)
                else:
                    print("⚠️ No image URL or b64 data in response")
                    return None
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Resize to exact TikTok dimensions using smart fit
                image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
                
                # Save the image
                filename = f"{self.output_dir}/{story_title.replace(' ', '_')}_scene_{scene_number}_openai.png"
                image.save(filename, 'PNG')
                print(f"✅ OpenAI image generated: {filename}")
                return filename
            else:
                print("⚠️ No image data in response")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI image generation error: {e}")
            return None
    
    def generate_philosophy_image(self, scene_data: dict, story_title: str) -> str:
        """Generate a classical, dark, mysterious image for philosophy story scene"""
        
        visual_desc = scene_data.get('visual_description', '')
        scene_text = scene_data.get('text', '')
        key_concept = scene_data.get('key_concept', '')
        scene_num = scene_data.get('scene_number', 1)
        
        # Use the same prompt style as Nano
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
        
        return self.generate_image(prompt, scene_num, story_title)


def test_openai_generation():
    """Test the OpenAI image generation with sample philosophy scene"""
    
    print("🧪 Testing OpenAI Image Generation for Philosophy Videos")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment")
        print("💡 Add it to your .env file: OPENAI_API_KEY=your-key-here")
        return None
    
    try:
        generator = OpenAIImageGenerator()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return None
    
    # Test scene data (same as Nano test)
    test_scene = {
        'scene_number': 1,
        'text': 'You sit in darkness, believing shadows on the wall are reality.',
        'visual_description': 'Dark cave with chained figures watching shadows on stone wall, flickering firelight creating dancing shadows',
        'key_concept': 'Illusion of Reality'
    }
    
    print(f"\n🎬 Test Scene: {test_scene['key_concept']}")
    print(f"📝 Description: {test_scene['visual_description']}")
    
    image_path = generator.generate_philosophy_image(test_scene, "Platos_Cave_OpenAI_Test")
    
    if image_path:
        print(f"\n✅ SUCCESS! Image saved to: {image_path}")
        print(f"🎯 Compare this with the Nano-generated images to evaluate quality")
    else:
        print(f"\n❌ Image generation failed")
    
    return image_path


def test_detailed_prompts():
    """Test with the detailed prompts from show_nano_prompts.py"""
    
    print("\n🎨 Testing with Detailed Nano-Style Prompts")
    print("=" * 60)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found")
        return []
    
    try:
        generator = OpenAIImageGenerator()
    except:
        return []
    
    # These are the exact prompts from show_nano_prompts.py
    detailed_prompts = [
        {
            "scene_number": 1,
            "philosophical_concept": "The Illusion of Reality",
            "image_prompt": "A haunting classical painting in the style of Caravaggio, showing silhouetted figures chained in a dark stone cave, their faces illuminated by flickering firelight as they stare at dancing shadows on the rough wall. The composition should be vertical (9:16), with dramatic chiaroscuro lighting creating deep shadows and golden highlights. The shadows on the wall should appear almost alive, suggesting movement and false reality. Rich color palette of deep browns, amber firelight, and mysterious blacks. The scene should evoke a sense of captivity and unknowing, with the chained figures representing humanity's bondage to illusion."
        },
        {
            "scene_number": 2,
            "philosophical_concept": "Philosophical Questioning", 
            "image_prompt": "A magnificent Renaissance-style portrait of an ancient Greek philosopher (representing Plato) in contemplative pose, surrounded by classical marble columns and scrolls. The figure should be depicted in profile, with one hand touching his bearded chin in thought, eyes gazing upward toward divine light streaming through classical architecture. The lighting should be reminiscent of Rembrandt's style - dramatic side lighting casting thoughtful shadows. Vertical composition optimized for TikTok. Color palette of rich blues, golden light, marble whites, and deep shadows. Ancient Greek architectural elements in the background should suggest timeless wisdom."
        },
        {
            "scene_number": 3,
            "philosophical_concept": "Liberation and Enlightenment",
            "image_prompt": "A dramatic painting in the style of Baroque masters, showing a human figure breaking free from heavy iron chains, emerging from darkness into brilliant divine light. The figure should be captured mid-motion, one foot still in shadow, one reaching toward a golden sunrise. Broken chains should be falling away dramatically. The light source should be overwhelming and ethereal, suggesting transcendence. Vertical composition with the figure positioned in the center, rising upward. The contrast between the dark cave below and radiant light above should be stark and emotional. Color palette emphasizing the transition from darkness to light - deep charcoals transitioning to brilliant golds and whites."
        }
    ]
    
    results = []
    for prompt_info in detailed_prompts[:2]:  # Test first 2 to save API calls
        print(f"\n🎬 Scene {prompt_info['scene_number']}: {prompt_info['philosophical_concept']}")
        
        image_path = generator.generate_image(
            prompt_info['image_prompt'],
            prompt_info['scene_number'],
            "Platos_Cave_Detailed"
        )
        
        if image_path:
            results.append(image_path)
            print(f"✅ Generated: {image_path}")
    
    print(f"\n📊 Generated {len(results)}/{len(detailed_prompts[:2])} images")
    return results


if __name__ == "__main__":
    print("🚀 OpenAI Image Generation Test")
    print("=" * 60)
    
    # Run basic test
    result = test_openai_generation()
    
    if result:
        # If basic test passes, try detailed prompts
        detailed_results = test_detailed_prompts()
        
        print("\n" + "=" * 60)
        print("🎯 COMPARISON CHECKLIST:")
        print("=" * 60)
        print("Compare OpenAI results with Nano results for:")
        print("  ✓ Classical painting aesthetic quality")
        print("  ✓ Chiaroscuro lighting accuracy")
        print("  ✓ Color palette richness")
        print("  ✓ Philosophical mood/atmosphere")
        print("  ✓ Vertical composition suitability")
        print("  ✓ Detail level and texture")
        print("\nIf OpenAI matches or exceeds Nano quality, consider switching!")

