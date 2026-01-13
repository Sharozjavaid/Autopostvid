#!/usr/bin/env python3
"""
Slideshow Generator - Creates TikTok-style slides with text burned into images
Uses GPT Image 1.5 via fal.ai for superior text rendering

Each slide looks like a typical TikTok slideshow:
- Background image (aesthetic, dark/moody)
- Clean white or black text overlaid (like CapCut/TikTok editor style)
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class SlideshowGenerator:
    """
    Generates TikTok-style slideshow images using GPT Image 1.5 via fal.ai.
    
    Each slide is like a TikTok slideshow page:
    - Background: aesthetic, dark/moody image
    - Text: Clean white/black text overlay (like CapCut editor)
    - Hook slide: "5 PHILOSOPHERS WHO CHANGED THE WORLD"
    - Content slides: "#1 SOCRATES" + quote
    
    Usage:
        gen = SlideshowGenerator()
        
        # Generate from topic (uses Gemini for script)
        paths = gen.generate_slideshow("5 philosophers who changed the world")
        
        # Generate from existing script
        paths = gen.generate_from_script(script_data)
        
        # Generate single slide
        path = gen.generate_slide(slide_data, "my_slideshow")
    """
    
    def __init__(self, quality: str = "medium"):
        self.output_dir = "generated_slideshows"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.quality = quality
        self._fal_available = None
        
        # Image settings for TikTok (9:16 vertical)
        self.image_size = "1024x1536"  # Vertical format for fal.ai
        
        print(f"🎴 SlideshowGenerator initialized (GPT Image 1.5 via fal.ai, quality: {self.quality})")
    
    @property
    def fal_available(self):
        """Check if fal.ai is available"""
        if self._fal_available is None:
            api_key = os.getenv('FAL_KEY')
            self._fal_available = bool(api_key)
            if self._fal_available:
                os.environ['FAL_KEY'] = api_key
        return self._fal_available
    
    def _build_slide_prompt(self, slide_data: Dict) -> str:
        """
        Build the image generation prompt for a TikTok-style slide.
        
        The goal is to mimic what you'd get from CapCut or TikTok's editor:
        - Aesthetic background image
        - Clean, bold white or black text overlaid
        - Text is the star - must be perfectly readable
        """
        
        slide_type = slide_data.get('slide_type', 'person')
        slide_number = slide_data.get('slide_number', 1)
        display_text = slide_data.get('display_text', '')
        subtitle = slide_data.get('subtitle', '')
        visual_description = slide_data.get('visual_description', '')
        person_name = slide_data.get('person_name', '')
        
        # Base TikTok slideshow style instruction
        tiktok_text_style = """
TEXT STYLING (CRITICAL - THIS IS THE MOST IMPORTANT PART):
- Text must be PERFECTLY CRISP and READABLE - this is a slideshow, text is everything
- Use clean, modern sans-serif font (like the fonts in TikTok/CapCut: bold, simple)
- WHITE text with a subtle black shadow/outline for maximum readability
- Text should be CENTERED and PROMINENT
- NO decorative/fancy fonts - just clean, bold, modern typography
- The text should look like it was added in a video editor (CapCut style)
- Text should pop against the background
"""
        
        if slide_type == 'hook':
            # Hook slide - bold title card
            prompt = f"""
Create a viral TikTok slideshow HOOK image. This is the first slide that needs to grab attention.

BACKGROUND:
{visual_description if visual_description else "Dark, moody, cinematic background. Could be abstract dark gradients, silhouettes, or atmospheric imagery. The background should NOT compete with the text."}

{tiktok_text_style}

TEXT TO DISPLAY (EXACTLY as written, ALL CAPS, centered):
"{display_text}"

The text should be LARGE, BOLD, and take up most of the image. This is a hook slide - the text IS the content.
Think: viral TikTok carousel first slide that makes people swipe.

Format: Vertical 9:16 mobile format (1080x1920 style proportions)
Style: Dark aesthetic, scroll-stopping, modern TikTok slideshow look
"""
        
        elif slide_type == 'person':
            # Person slide - number + name + subtitle
            prompt = f"""
Create a TikTok slideshow image featuring {person_name}.

BACKGROUND:
{visual_description if visual_description else f"Dark, moody portrait-style background suggesting {person_name}. Classical/historical aesthetic with dark shadows and subtle warm highlights."}
The background should be visible but NOT compete with the text overlay.

{tiktok_text_style}

TEXT TO DISPLAY (in this exact layout):

TOP OF IMAGE:
"#{slide_number}" - Large, bold white text

CENTER OF IMAGE:
"{display_text}" - Large, bold white text (this is the main name/title)

LOWER CENTER (if subtitle provided):
"{subtitle}" - Smaller white text, still bold and readable

Layout like a TikTok slideshow: numbered list item with the main subject and a punchy one-liner underneath.

Format: Vertical 9:16 mobile format
Style: Dark aesthetic, TikTok carousel style, modern and clean typography
"""
        
        elif slide_type == 'quote':
            # Quote slide
            prompt = f"""
Create a TikTok slideshow QUOTE image.

BACKGROUND:
{visual_description if visual_description else "Dark, atmospheric, contemplative background. Abstract or minimal so the quote can shine."}

{tiktok_text_style}

TEXT TO DISPLAY:

TOP:
"#{slide_number}" - in bold white

CENTER (the quote):
"{subtitle}" - in elegant but bold white text, slightly larger

BOTTOM ATTRIBUTION:
"— {display_text}" - smaller white text

This is a quote slide - the words are the star. Make them crisp and impactful.

Format: Vertical 9:16 mobile format
Style: Inspirational TikTok quote post aesthetic
"""
        
        elif slide_type == 'outro':
            # Outro/CTA slide
            prompt = f"""
Create a TikTok slideshow OUTRO/call-to-action image.

BACKGROUND:
{visual_description if visual_description else "Dark, powerful, cinematic background. Could be abstract gradients or atmospheric imagery."}

{tiktok_text_style}

TEXT TO DISPLAY (centered, impactful):
"{display_text}"
{f'"{subtitle}"' if subtitle else ''}

This is the closing slide - should leave an impression or prompt action (follow, like, share).

Format: Vertical 9:16 mobile format
Style: TikTok carousel closing slide, bold and memorable
"""
        
        else:
            # Generic content slide
            prompt = f"""
Create a TikTok slideshow content image.

BACKGROUND:
{visual_description if visual_description else "Dark, aesthetic background that doesn't compete with text."}

{tiktok_text_style}

TEXT TO DISPLAY:
"{display_text}"
{f'"{subtitle}"' if subtitle else ''}

Format: Vertical 9:16 mobile format
Style: Modern TikTok slideshow aesthetic
"""
        
        return prompt.strip()
    
    def generate_slide(self, slide_data: Dict, slideshow_name: str) -> Optional[str]:
        """
        Generate a single slide image using GPT Image 1.5 via fal.ai.
        
        Args:
            slide_data: Dictionary with slide_number, slide_type, display_text, etc.
            slideshow_name: Name for the output file
        
        Returns:
            Path to generated image, or None if failed
        """
        if not self.fal_available:
            print("❌ fal.ai not available. Set FAL_KEY in .env file.")
            return None
        
        slide_number = slide_data.get('slide_number', 0)
        prompt = self._build_slide_prompt(slide_data)
        
        try:
            import fal_client
            import requests
            from PIL import Image, ImageOps
            import io
            
            print(f"  🎨 Generating slide {slide_number} with GPT Image 1.5...")
            print(f"     Type: {slide_data.get('slide_type', 'unknown')}")
            print(f"     Text: {slide_data.get('display_text', '')[:50]}...")
            
            # Use fal.ai's GPT Image 1.5
            result = fal_client.subscribe(
                "fal-ai/gpt-image-1.5",
                arguments={
                    "prompt": prompt,
                    "image_size": self.image_size,
                    "quality": self.quality,
                    "num_images": 1,
                    "output_format": "png"
                },
            )
            
            # Extract image URL or base64 data
            images = result.get('images', [])
            if not images:
                print(f"     ❌ No images in response")
                return None
            
            image_data = images[0]
            image_url = image_data.get('url')
            
            if not image_url:
                print(f"     ❌ No URL in image data")
                return None
            
            # Handle base64 data URIs (returned when sync_mode=true)
            if image_url.startswith('data:'):
                # Parse base64 data URI: data:image/png;base64,<data>
                import base64 as b64
                try:
                    # Split to get the base64 part after the comma
                    header, encoded_data = image_url.split(',', 1)
                    image_bytes = b64.b64decode(encoded_data)
                    image = Image.open(io.BytesIO(image_bytes))
                    print(f"     📦 Decoded base64 image data")
                except Exception as e:
                    print(f"     ❌ Failed to decode base64 image: {e}")
                    return None
            else:
                # Regular HTTP URL - download the image
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            
            # Resize to exact TikTok dimensions (1080x1920)
            image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
            
            # Save
            safe_name = "".join(c for c in slideshow_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"{self.output_dir}/{safe_name}_slide_{slide_number}.png"
            image.save(filename, 'PNG')
            
            print(f"     ✅ Saved: {filename}")
            return filename
                
        except Exception as e:
            print(f"     ❌ Error generating slide {slide_number}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_from_script(self, script_data: Dict) -> List[str]:
        """
        Generate all slides from a slideshow script.
        
        Args:
            script_data: Dictionary with 'title' and 'slides' array
        
        Returns:
            List of paths to generated images
        """
        title = script_data.get('title', 'Slideshow')
        slides = script_data.get('slides', [])
        
        if not slides:
            print("❌ No slides found in script")
            return []
        
        print(f"🎴 Generating slideshow: {title}")
        print(f"   Total slides: {len(slides)}")
        print(f"   Using: GPT Image 1.5 via fal.ai")
        
        image_paths = []
        
        for slide in slides:
            path = self.generate_slide(slide, title)
            if path:
                image_paths.append(path)
        
        print(f"✅ Generated {len(image_paths)}/{len(slides)} slides")
        return image_paths
    
    def generate_slideshow(self, topic: str) -> Dict:
        """
        Generate a complete slideshow from a topic.
        
        Uses Gemini to generate the script, then GPT Image 1.5 to generate images.
        
        Args:
            topic: The slideshow topic (e.g., "5 philosophers who changed the world")
        
        Returns:
            Dictionary with 'script' and 'image_paths'
        """
        from gemini_handler import GeminiHandler
        
        print(f"🎴 Creating TikTok slideshow for: {topic}")
        print("=" * 50)
        
        # Check fal.ai availability
        if not self.fal_available:
            print("❌ FAL_KEY not found. GPT Image 1.5 requires fal.ai API key.")
            return {'script': None, 'image_paths': []}
        
        # Step 1: Generate script with Gemini
        print("📝 Step 1: Generating script with Gemini...")
        gemini = GeminiHandler()
        script_data = gemini.generate_slideshow_script(topic)
        
        if not script_data:
            print("❌ Failed to generate script")
            return {'script': None, 'image_paths': []}
        
        print(f"   ✅ Script generated: {script_data.get('title', 'Unknown')}")
        print(f"   📊 Slides: {len(script_data.get('slides', []))}")
        
        # Step 2: Generate images with GPT Image 1.5
        print("\n🎨 Step 2: Generating slide images with GPT Image 1.5...")
        image_paths = self.generate_from_script(script_data)
        
        print("\n" + "=" * 50)
        print(f"✅ TikTok slideshow complete!")
        print(f"   Images: {len(image_paths)}")
        print(f"   Output: {self.output_dir}/")
        
        return {
            'script': script_data,
            'image_paths': image_paths
        }


def check_slideshow_available() -> bool:
    """Check if slideshow generation is available (FAL_KEY is set)."""
    api_key = os.getenv('FAL_KEY')
    return bool(api_key)


# Convenience function for quick generation
def create_slideshow(topic: str, quality: str = "medium") -> Dict:
    """
    Quick function to generate a slideshow from a topic.
    
    Args:
        topic: Slideshow topic (e.g., "5 Stoic philosophers")
        quality: Image quality - "low" (fast), "medium", or "high"
    
    Returns:
        Dictionary with 'script' and 'image_paths'
    """
    gen = SlideshowGenerator(quality=quality)
    return gen.generate_slideshow(topic)


# Test
if __name__ == "__main__":
    print("🧪 Testing SlideshowGenerator (GPT Image 1.5)")
    print("=" * 50)
    
    # Check if fal.ai is available
    api_key = os.getenv('FAL_KEY')
    if not api_key:
        print("❌ FAL_KEY not found. Please set it in .env")
        exit(1)
    
    # Test with a sample topic
    result = create_slideshow("5 Stoic philosophers and their most powerful ideas")
    
    if result['image_paths']:
        print(f"\n🎉 Success! Generated {len(result['image_paths'])} slides")
        for path in result['image_paths']:
            print(f"   - {path}")
    else:
        print("\n❌ No images generated")
