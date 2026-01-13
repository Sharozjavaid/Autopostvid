#!/usr/bin/env python3
"""
GPT Image 1.5 Generator via fal.ai

Uses fal-ai/gpt-image-1.5 for high-quality image generation with consistent
bold text overlays. This is the preferred image generator for philosophy videos
because:
1. Consistent typography with bold text overlays
2. Great quality at "low" setting (fast + cheap)
3. Reliable text rendering for slide subjects
"""

import os
import fal_client
import requests
from PIL import Image, ImageOps
import io
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv()


class GPTImageGenerator:
    """Generate images using fal.ai's GPT Image 1.5 model.
    
    Supports two modes:
    1. Background-only (RECOMMENDED): Generate clean backgrounds, add text with Pillow
    2. Text-burned (LEGACY): Generate images with AI-burned text overlays
    """
    
    # Background-only style (NO TEXT - for programmatic text overlay)
    BACKGROUND_STYLE_TEMPLATE = """Dark moody classical oil painting style, dramatic Caravaggio chiaroscuro lighting, 
Renaissance/Baroque aesthetic, rich deep colors (burgundy, gold, deep blue), 
mysterious shadows with golden highlights, philosophical atmosphere.
{visual_description}

CRITICAL: Do NOT include any text, words, letters, numbers, or typography in the image.
Leave the CENTER of the image relatively clean for text overlay.
Vertical 9:16 aspect ratio, mobile format."""
    
    # Legacy style with bold text overlay (DEPRECATED - use background + Pillow instead)
    STYLE_TEMPLATE = """Dark moody classical oil painting style, dramatic Caravaggio chiaroscuro lighting, 
Renaissance/Baroque aesthetic, rich deep colors (burgundy, gold, deep blue), 
mysterious shadows with golden highlights, philosophical atmosphere.
{visual_description}
Bold text overlay prominently displaying: "{slide_subject}"
The text should be large, centered, golden/yellow metallic with slight 3D emboss effect,
cinematic movie poster typography style, highly legible against the dark background.
Vertical 9:16 aspect ratio, mobile format."""

    def __init__(self, api_key: str = None, quality: str = "low"):
        """
        Initialize the GPT Image 1.5 generator.
        
        Args:
            api_key: fal.ai API key (defaults to FAL_KEY env var)
            quality: Image quality - "low" (fast/cheap), "medium", or "high"
        """
        self.api_key = api_key or os.getenv('FAL_KEY')
        if not self.api_key:
            raise ValueError("FAL_KEY not found. Please set FAL_KEY in .env file")
        
        # Set the API key for fal_client
        os.environ['FAL_KEY'] = self.api_key
        
        self.quality = quality
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Model endpoint
        self.model_id = "fal-ai/gpt-image-1.5"
        
        print(f"✅ GPT Image 1.5 Generator initialized (quality: {quality})")
    
    def generate_image(
        self,
        prompt: str,
        scene_number: int,
        story_title: str,
        image_size: str = "1024x1536",  # Vertical format
        output_format: str = "png"
    ) -> Optional[str]:
        """
        Generate a single image using GPT Image 1.5.
        
        Args:
            prompt: The full image generation prompt (should include bold text overlay instruction)
            scene_number: Scene number for filename
            story_title: Story title for filename
            image_size: Image size (default 1024x1536 for vertical)
            output_format: Output format (png or jpg)
            
        Returns:
            Local path to saved image, or None on failure
        """
        print(f"\n🎨 Generating image for scene {scene_number}...")
        print(f"📝 Prompt: {prompt[:150]}...")
        
        try:
            # Use subscribe method for reliable results with proper URLs
            # (streaming can return incomplete/different formats)
            print(f"   Calling fal.ai API...")
            
            def on_queue_update(update):
                if hasattr(update, 'logs') and update.logs:
                    for log in update.logs:
                        msg = log.get('message', str(log)) if isinstance(log, dict) else str(log)
                        print(f"   [fal] {msg}")
            
            result = fal_client.subscribe(
                self.model_id,
                arguments={
                    "prompt": prompt,
                    "image_size": image_size,
                    "background": "auto",
                    "quality": self.quality,
                    "num_images": 1,
                    "output_format": output_format
                },
                with_logs=True,
                on_queue_update=on_queue_update,
            )
            
            # Extract image URL or base64 data
            # Debug: log the response structure
            print(f"   📦 Response keys: {result.keys() if isinstance(result, dict) else type(result)}")
            
            images = result.get('images', [])
            if not images:
                print(f"❌ No images in response: {result}")
                return None
            
            image_data = images[0]
            print(f"   📦 Image data keys: {image_data.keys() if isinstance(image_data, dict) else type(image_data)}")
            
            image_url = image_data.get('url')
            
            if not image_url:
                # Also check for 'file_data' field which might contain base64
                file_data = image_data.get('file_data')
                if file_data:
                    print(f"   📦 Found file_data instead of url, using that...")
                    image_url = file_data
                else:
                    print(f"❌ No URL in image data: {image_data}")
                    return None
            
            print(f"   📦 URL type: {'base64 data URI' if image_url.startswith('data:') else 'HTTP URL'}")
            
            # Handle base64 data URIs (returned when sync_mode=true)
            if image_url.startswith('data:'):
                # Parse base64 data URI: data:image/png;base64,<data>
                import base64 as b64
                try:
                    # Split to get the base64 part after the comma
                    header, encoded_data = image_url.split(',', 1)
                    image_bytes = b64.b64decode(encoded_data)
                    image = Image.open(io.BytesIO(image_bytes))
                    print(f"   📦 Decoded base64 image data")
                except Exception as e:
                    print(f"❌ Failed to decode base64 image: {e}")
                    return None
            else:
                # Regular HTTP URL - download the image
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            
            # Resize to exact TikTok dimensions
            image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
            
            # Save the image
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            filename = f"{self.output_dir}/{safe_title}_scene_{scene_number}_gpt15.png"
            image.save(filename, 'PNG')
            
            print(f"✅ Image saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ GPT Image 1.5 generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_philosophy_image(
        self,
        scene_data: Dict,
        story_title: str,
        story_data: Dict = None
    ) -> Optional[str]:
        """
        Generate a philosophy-themed image for a scene with bold text overlay.
        
        This is the main method used by the pipeline. It:
        1. Extracts the visual description and slide subject from scene data
        2. Builds a prompt using the classical philosophy style template
        3. Generates the image with bold text overlay
        
        Args:
            scene_data: Scene dictionary with visual_description, slide_subject, etc.
            story_title: Title of the story
            story_data: Optional full story data for additional context (list_items, etc.)
            
        Returns:
            Path to saved image, or None on failure
        """
        scene_num = scene_data.get('scene_number', 1)
        visual_desc = scene_data.get('visual_description', 'Classical philosophical scene')
        
        # Get the slide subject - this is what appears as bold text overlay
        slide_subject = self._get_slide_subject(scene_data, scene_num, story_data)
        
        print(f"\n🎬 Scene {scene_num}")
        print(f"📝 Visual: {visual_desc[:80]}...")
        print(f"🏷️  Subject: {slide_subject}")
        
        # Build the full prompt with our style template
        prompt = self.STYLE_TEMPLATE.format(
            visual_description=visual_desc,
            slide_subject=slide_subject
        )
        
        return self.generate_image(
            prompt=prompt,
            scene_number=scene_num,
            story_title=story_title
        )
    
    def _get_slide_subject(
        self, 
        scene_data: Dict, 
        scene_number: int, 
        story_data: Dict = None
    ) -> str:
        """
        Extract or build the slide subject (bold text overlay) for a scene.
        
        Priority:
        1. scene_data['slide_subject'] - if explicitly provided by script generator
        2. scene_data['display_text'] - for slideshow-style content
        3. Built from list_item + person_name (e.g., "#1 SOCRATES")
        4. scene_data['key_concept'] - fallback to key concept
        5. "SCENE {n}" - ultimate fallback
        
        Args:
            scene_data: Scene dictionary
            scene_number: Scene number (1-indexed)
            story_data: Optional story data with list_items
        
        Returns:
            The text to display as bold overlay
        """
        # 1. Direct slide_subject from script generator (preferred)
        if scene_data.get('slide_subject'):
            return scene_data['slide_subject'].upper()
        
        # 2. Display text (for slideshow content)
        if scene_data.get('display_text'):
            return scene_data['display_text'].upper()
        
        # 3. Build from list_item and person_name
        list_item = scene_data.get('list_item', 0)
        list_items = (story_data or {}).get('list_items', [])
        
        if list_item and list_item > 0:
            # Find matching person/concept from list_items
            person_name = scene_data.get('person_name', '')
            
            if not person_name and list_items:
                matching_item = next(
                    (item for item in list_items if item.get('number') == list_item), 
                    None
                )
                if matching_item:
                    person_name = matching_item.get('name', '')
            
            if person_name:
                return f"#{list_item} {person_name.upper()}"
        
        # 4. Key concept
        key_concept = scene_data.get('key_concept', '')
        if key_concept:
            # For hook/intro scenes
            if list_item == 0 and scene_number == 1:
                if 'hook' in key_concept.lower():
                    return "THE TRUTH REVEALED"
                return key_concept.upper()
            # For outro scenes
            elif list_item == 0 and scene_number > 1:
                if 'call to action' in key_concept.lower() or 'outro' in key_concept.lower():
                    return "CHOOSE YOUR PATH"
                return key_concept.upper()
            # For regular concept scenes
            return key_concept.upper()
        
        # 5. Fallback
        return f"SCENE {scene_number}"
    
    def generate_background(
        self,
        visual_description: str,
        scene_number: int,
        story_title: str,
        image_size: str = "1024x1536"
    ) -> Optional[str]:
        """
        Generate a BACKGROUND-ONLY image (no text).
        
        This is the RECOMMENDED method for cost-effective image generation.
        Use this with TextOverlay.create_slide() to add text programmatically.
        
        Args:
            visual_description: Description of what the background should show
            scene_number: Scene number for filename
            story_title: Story title for filename
            image_size: Image size (default vertical)
            
        Returns:
            Path to saved background image, or None on failure
        """
        print(f"\n🎨 Generating background for scene {scene_number}...")
        
        # Build background-only prompt (NO text)
        prompt = self.BACKGROUND_STYLE_TEMPLATE.format(
            visual_description=visual_description
        )
        
        print(f"📝 Prompt: {prompt[:120]}...")
        
        try:
            result = fal_client.subscribe(
                self.model_id,
                arguments={
                    "prompt": prompt,
                    "image_size": image_size,
                    "background": "auto",
                    "quality": self.quality,
                    "num_images": 1,
                    "output_format": "png"
                },
            )
            
            images = result.get('images', [])
            if not images:
                print(f"❌ No images in response")
                return None
            
            image_data = images[0]
            image_url = image_data.get('url')
            
            if not image_url:
                return None
            
            # Handle base64 or URL
            if image_url.startswith('data:'):
                import base64 as b64
                header, encoded_data = image_url.split(',', 1)
                image_bytes = b64.b64decode(encoded_data)
                image = Image.open(io.BytesIO(image_bytes))
            else:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            
            # Resize to TikTok dimensions
            image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
            
            # Save with _bg suffix to distinguish from final images
            safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            filename = f"{self.output_dir}/{safe_title}_scene_{scene_number}_bg.png"
            image.save(filename, 'PNG')
            
            print(f"✅ Background saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Background generation error: {e}")
            return None
    
    def generate_batch(
        self,
        scenes: List[Dict],
        story_title: str,
        story_data: Dict = None,
        progress_callback=None,
        background_only: bool = False
    ) -> List[str]:
        """
        Generate images for all scenes in a story.
        
        Args:
            scenes: List of scene dictionaries
            story_title: Title of the story
            story_data: Optional full story data for context
            progress_callback: Optional callback(current, total, status)
            background_only: If True, generate backgrounds without text (for Pillow overlay)
            
        Returns:
            List of paths to saved images
        """
        mode = "backgrounds (for text overlay)" if background_only else "images with AI text"
        print(f"\n🎥 Generating {len(scenes)} {mode} with GPT Image 1.5...")
        
        image_paths = []
        
        for i, scene in enumerate(scenes):
            if progress_callback:
                progress_callback(i + 1, len(scenes), f"Generating image {i + 1}/{len(scenes)}")
            
            if background_only:
                visual_desc = scene.get('visual_description', 'Classical philosophical scene')
                image_path = self.generate_background(
                    visual_description=visual_desc,
                    scene_number=scene.get('scene_number', i + 1),
                    story_title=story_title
                )
            else:
                image_path = self.generate_philosophy_image(
                    scene_data=scene,
                    story_title=story_title,
                    story_data=story_data
                )
            
            if image_path:
                image_paths.append(image_path)
            else:
                print(f"⚠️ Failed to generate image for scene {scene.get('scene_number', i + 1)}")
        
        print(f"\n✅ Generated {len(image_paths)}/{len(scenes)} images")
        return image_paths


def check_gpt_image_available() -> bool:
    """Check if GPT Image 1.5 is available (FAL_KEY is set)."""
    api_key = os.getenv('FAL_KEY')
    return bool(api_key)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("GPT Image 1.5 Generator Test")
    print("=" * 60)
    
    if not check_gpt_image_available():
        print("❌ FAL_KEY not found in environment. Please set it in .env")
        exit(1)
    
    # Initialize generator
    gen = GPTImageGenerator(quality="low")
    
    # Test with a simple prompt (like user's example)
    test_prompt = """Dark moody classical oil painting style, dramatic Caravaggio lighting.
Ancient Greek philosopher Socrates with beard, wise contemplative expression.
Bold text overlay prominently displaying: "#1 SOCRATES"
The text should be large, centered, golden/yellow metallic with slight 3D emboss effect,
cinematic movie poster typography style, highly legible against the dark background.
Vertical 9:16 aspect ratio."""
    
    print("\n🧪 Testing basic image generation...")
    result = gen.generate_image(
        prompt=test_prompt,
        scene_number=1,
        story_title="GPT15_Test"
    )
    
    if result:
        print(f"\n✅ Test successful! Image saved to: {result}")
    else:
        print("\n❌ Test failed!")
    
    # Test with scene data (like it would be used in pipeline)
    print("\n🧪 Testing scene-based generation...")
    
    test_scene = {
        "scene_number": 2,
        "text": "Aristotle invented logic and taught us that excellence is a habit.",
        "visual_description": "Ancient Greek philosopher Aristotle in classical robes, teaching students in a Greek academy",
        "slide_subject": "#2 ARISTOTLE",
        "key_concept": "Excellence",
        "list_item": 2
    }
    
    test_story = {
        "title": "5 Philosophers Who Changed The World",
        "list_items": [
            {"number": 1, "name": "Socrates"},
            {"number": 2, "name": "Aristotle"},
        ]
    }
    
    result2 = gen.generate_philosophy_image(
        scene_data=test_scene,
        story_title=test_story["title"],
        story_data=test_story
    )
    
    if result2:
        print(f"\n✅ Scene test successful! Image saved to: {result2}")
    else:
        print("\n❌ Scene test failed!")
