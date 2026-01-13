#!/usr/bin/env python3
"""
TikTok Slideshow Generator - Complete pipeline for creating viral slideshows

This module orchestrates the complete workflow:
1. AI generates the slideshow script (text content for each slide)
2. AI generates background images (aesthetic, dark/moody)
3. Text is burned onto images programmatically (consistent, clean styling)

The result looks like the image you shared: 
- Clean background image (person on beach, moody sky)
- Bold text overlay (TikTok/CapCut style)
- Professional, scroll-stopping aesthetic

Usage:
    from tiktok_slideshow import TikTokSlideshow
    
    slideshow = TikTokSlideshow()
    result = slideshow.create("6 philosophical practices for inner peace")
    
    # Result contains:
    # - script: The generated slideshow script
    # - slides: List of slide data with text
    # - image_paths: Paths to final images with text burned in
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class TikTokSlideshow:
    """
    Complete TikTok slideshow generation pipeline.
    
    Workflow:
    1. Generate script with Gemini (slide text, visual descriptions)
    2. Generate background images with AI (fal.ai or OpenAI)
    3. Burn text onto images with Pillow (TextOverlay module)
    
    This approach gives you:
    - Perfect text control (exact font, size, positioning)
    - Consistent styling across all slides
    - Lower cost (simpler background images to generate)
    - Fast iteration (change text without regenerating images)
    """
    
    # Available fal.ai models for background generation
    FAL_MODELS = {
        "gpt15": {
            "id": "fal-ai/gpt-image-1.5",
            "name": "GPT Image 1.5",
            "description": "High quality, good for detailed scenes",
            "image_size": "1024x1536",
            "extra_args": {
                "quality": "low",
                "background": "auto"
            }
        },
        "flux": {
            "id": "fal-ai/flux/schnell",
            "name": "Flux Schnell 1.1",
            "description": "Fast, good quality, great for moody aesthetics",
            "image_size": "portrait_16_9",  # Correct format for Flux API
            "extra_args": {
                "num_inference_steps": 4,
                "guidance_scale": 3.5,
                "enable_safety_checker": True
            }
        }
    }
    
    def __init__(
        self,
        output_dir: str = "generated_slideshows",
        image_generator: str = "fal",  # "fal", "openai", or "dalle"
        fal_model: str = "gpt15"  # "gpt15" (recommended) or "flux"
    ):
        """
        Initialize the slideshow generator.
        
        This is a SLIDESHOW-ONLY pipeline:
        - Generates script with Gemini
        - Generates background images with fal.ai (Flux or GPT 1.5) or OpenAI
        - Burns text onto images with Pillow (TextOverlay)
        - Outputs: PNG slides ready for TikTok/Instagram
        
        NO voice generation, NO video assembly - just slides.
        
        Args:
            output_dir: Directory for output images
            image_generator: Which service to use for backgrounds:
                - "fal": fal.ai (uses fal_model setting)
                - "openai" or "dalle": OpenAI DALL-E 3
            fal_model: Which fal.ai model to use (if image_generator="fal"):
                - "gpt15": GPT Image 1.5 (detailed, high quality) - RECOMMENDED
                - "flux": Flux Schnell 1.1 (faster, slightly lower quality)
        """
        self.output_dir = output_dir
        self.backgrounds_dir = os.path.join(output_dir, "backgrounds")
        self.image_generator = image_generator
        self.fal_model = fal_model
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.backgrounds_dir, exist_ok=True)
        
        # Get model info for display
        if image_generator == "fal" and fal_model in self.FAL_MODELS:
            model_info = self.FAL_MODELS[fal_model]
            bg_name = f"fal.ai {model_info['name']}"
        elif image_generator in ["openai", "dalle"]:
            bg_name = "OpenAI DALL-E 3"
        else:
            bg_name = image_generator
        
        print(f"🎴 TikTokSlideshow initialized (SLIDESHOW-ONLY pipeline)")
        print(f"   📁 Output: {self.output_dir}")
        print(f"   🎨 Background generator: {bg_name}")
        print(f"   📝 Text overlay: Pillow (programmatic)")
        print(f"   🚫 No voice/video - slides only")
    
    def _generate_script(self, topic: str) -> Optional[Dict]:
        """
        Generate slideshow script using Gemini.
        
        Returns structured data with slides containing:
        - slide_number, slide_type
        - display_text (main text for slide)
        - subtitle (secondary text)
        - visual_description (for background image generation)
        """
        from gemini_handler import GeminiHandler
        
        print("📝 Generating slideshow script with Gemini...")
        gemini = GeminiHandler()
        script = gemini.generate_slideshow_script(topic)
        
        if script:
            print(f"   ✅ Script generated: {script.get('title', 'Unknown')}")
            print(f"   📊 Slides: {len(script.get('slides', []))}")
        else:
            print("   ❌ Failed to generate script")
        
        return script
    
    def _generate_background_prompt(self, slide: Dict) -> str:
        """
        Create an optimized prompt for background image generation.
        
        The prompt focuses on creating a clean, aesthetic background
        WITHOUT text - text will be added programmatically.
        """
        visual_description = slide.get('visual_description', '')
        slide_type = slide.get('slide_type', 'content')
        display_text = slide.get('display_text', '')
        person_name = slide.get('person_name', '')
        
        # Enhanced base style for TikTok-worthy images
        base_style = """
STYLE REQUIREMENTS:
- Vertical format (9:16 aspect ratio, 1080x1920 pixels)
- TikTok/Instagram aesthetic - scroll-stopping, visually striking
- Clean composition with space for text overlay in center
- High contrast, bold colors OR moody dark tones
- Professional, cinematic quality
- Simple, focused - ONE main subject, not cluttered

CRITICAL: 
- Do NOT include any text, words, letters, numbers, or typography
- Do NOT include watermarks or logos
- This is a BACKGROUND ONLY - text will be added separately
- Leave the CENTER of the image relatively clean for text overlay
"""
        
        # Determine the subject from the slide content
        subject = person_name or display_text or "philosophical concept"
        
        if slide_type == 'hook':
            prompt = f"""
Create a POWERFUL, scroll-stopping background image for a viral TikTok slideshow hook.

SUBJECT: {visual_description if visual_description else f"Epic, dramatic scene related to: {subject}"}

MOOD: Epic, mysterious, makes you STOP scrolling
- Think: movie poster energy, dramatic lighting
- Could be: silhouettes, dramatic skies, iconic imagery
- Feel: "Something important is about to be revealed"

{base_style}

Make it feel like the opening shot of an epic documentary or movie trailer.
"""
        
        elif slide_type == 'person' or person_name:
            # For slides about specific people, be very literal
            prompt = f"""
Create an artistic background image featuring or representing: {person_name if person_name else display_text}

VISUAL: {visual_description if visual_description else f"Artistic representation of {person_name or display_text} - silhouette, stylized portrait, or scene from their era"}

GUIDELINES FOR PERSON-BASED SLIDES:
- If ancient philosopher (Marcus Aurelius, Socrates, etc): Classical art style, marble textures, Roman/Greek setting, warm golden candlelight
- If modern figure (Steve Jobs, Elon Musk, etc): Clean minimalist style, modern aesthetic, their iconic look/setting
- If religious/spiritual (Buddha, Confucius): Serene, peaceful, warm tones, nature elements
- Make the person RECOGNIZABLE through their iconic elements (Jobs = black turtleneck, Aurelius = Roman emperor robes, etc.)

{base_style}
"""
        
        elif slide_type == 'lesson' or slide_type == 'reason':
            prompt = f"""
Create an aesthetic background that visually represents this concept:

CONCEPT: {visual_description if visual_description else f"Visual metaphor for: {display_text}"}

MOOD: Thoughtful, inspiring, makes the viewer pause and think
- Simple, clean composition
- Could be: metaphorical imagery, symbolic objects, atmospheric scenes
- The image should SUPPORT the message, not distract from it

{base_style}

Think: What image would make this lesson/reason hit harder?
"""
        
        elif slide_type == 'quote':
            prompt = f"""
Create a contemplative, minimalist background for a philosophical quote.

VISUAL: {visual_description if visual_description else "Soft, atmospheric scene - gradients, silhouettes, or nature that evokes deep thinking"}

MOOD: Peaceful, contemplative, lets the words shine
- Keep it SIMPLE - the quote is the star
- Soft lighting, muted or warm tones
- Could be: abstract gradients, peaceful landscapes, minimal scenes

{base_style}
"""
        
        elif slide_type == 'outro':
            prompt = f"""
Create an inspiring, powerful closing image for a TikTok slideshow.

VISUAL: {visual_description if visual_description else "Inspiring scene - figure at sunrise, path into light, or uplifting imagery suggesting possibility and action"}

MOOD: Hopeful, inspiring, calls to action
- Feel like a NEW BEGINNING
- Could be: sunrise, open road, figure facing horizon, light breaking through
- Makes the viewer want to TAKE ACTION

{base_style}
"""
        
        else:
            # Default for any other slide type
            prompt = f"""
Create an aesthetic TikTok background image.

VISUAL: {visual_description if visual_description else f"Atmospheric, visually interesting background related to: {subject}"}

{base_style}
"""
        
        return prompt.strip()
    
    def _generate_background_fal(self, prompt: str, output_path: str) -> Optional[str]:
        """Generate background image using fal.ai.
        
        Supports multiple models:
        - Flux Schnell 1.1: Fast, good for moody aesthetics
        - GPT Image 1.5: Detailed, slightly slower
        """
        try:
            import fal_client
            import requests
            from PIL import Image, ImageOps
            import io
            import base64
            
            api_key = os.getenv('FAL_KEY')
            if not api_key:
                print("   ❌ FAL_KEY not found")
                return None
            
            # Get model config
            model_config = self.FAL_MODELS.get(self.fal_model, self.FAL_MODELS["flux"])
            model_id = model_config["id"]
            model_name = model_config["name"]
            
            print(f"   🎨 Using {model_name}...")
            
            # Build arguments based on model
            arguments = {
                "prompt": prompt,
                "image_size": model_config["image_size"],
                "num_images": 1,
                "output_format": "png" if self.fal_model == "gpt15" else "jpeg",
                **model_config.get("extra_args", {})
            }
            
            result = fal_client.subscribe(
                model_id,
                arguments=arguments,
            )
            
            images = result.get('images', [])
            if not images:
                print("   ❌ No images in response")
                return None
            
            image_url = images[0].get('url')
            if not image_url:
                print("   ❌ No URL in response")
                return None
            
            # Handle base64 data URIs or regular URLs
            if image_url.startswith('data:'):
                # Parse base64 data URI
                header, encoded_data = image_url.split(',', 1)
                image_bytes = base64.b64decode(encoded_data)
                img = Image.open(io.BytesIO(image_bytes))
            else:
                # Download from URL
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
            
            # Resize to exact TikTok dimensions (1080x1920)
            img = ImageOps.fit(img, (1080, 1920), method=Image.Resampling.LANCZOS)
            img.save(output_path, 'PNG')
            
            print(f"   ✅ Background saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ fal.ai {self.fal_model} error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_background_openai(self, prompt: str, output_path: str) -> Optional[str]:
        """Generate background image using OpenAI DALL-E."""
        try:
            from openai import OpenAI
            import requests
            from PIL import Image
            import io
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("   ❌ OPENAI_API_KEY not found")
                return None
            
            client = OpenAI(api_key=api_key)
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",  # Vertical format
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download and save
            img_response = requests.get(image_url, stream=True)
            img_response.raise_for_status()
            
            img = Image.open(io.BytesIO(img_response.content))
            img.save(output_path, 'PNG')
            
            return output_path
            
        except Exception as e:
            print(f"   ❌ OpenAI error: {e}")
            return None
    
    def _generate_background(self, slide: Dict, slideshow_name: str, slide_index: int) -> Optional[str]:
        """Generate a background image for a slide."""
        prompt = self._generate_background_prompt(slide)
        
        safe_name = "".join(c for c in slideshow_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        output_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{slide_index}.png")
        
        print(f"   🎨 Generating background for slide {slide_index}...")
        
        if self.image_generator == "fal":
            return self._generate_background_fal(prompt, output_path)
        elif self.image_generator in ["openai", "dalle"]:
            return self._generate_background_openai(prompt, output_path)
        else:
            print(f"   ❌ Unknown image generator: {self.image_generator}")
            return None
    
    def _create_fallback_background(self, output_path: str) -> str:
        """Create a simple gradient background as fallback."""
        from text_overlay import TextOverlay
        
        overlay = TextOverlay()
        overlay.create_solid_background(output_path, color=(20, 25, 35), gradient=True)
        return output_path
    
    def _burn_text_onto_slide(
        self,
        background_path: str,
        slide: Dict,
        output_path: str,
        font_style: str = None,
        font_name: str = None,
        visual_style: str = "modern"
    ) -> str:
        """Burn text onto a background image.
        
        Args:
            background_path: Path to background image
            slide: Slide data dictionary
            output_path: Output path for final image
            font_style: Font style ("bold", "italic", "elegant")
            font_name: Specific font ("inter", "playfair", "bebas", "cinzel", etc.)
            visual_style: Visual style ("modern", "elegant", "philosophaire", "bold", "minimal")
        """
        from text_overlay import TextOverlay
        
        overlay = TextOverlay()
        slide_type = slide.get('slide_type', 'content')
        
        if slide_type == 'hook':
            return overlay.create_hook_slide(
                background_path=background_path,
                output_path=output_path,
                hook_text=slide.get('display_text', ''),
                style=visual_style,
                font_style=font_style,
                font_name=font_name
            )
        elif slide_type == 'outro':
            return overlay.create_outro_slide(
                background_path=background_path,
                output_path=output_path,
                text=slide.get('display_text', ''),
                subtitle=slide.get('subtitle'),
                style=visual_style,
                font_style=font_style,
                font_name=font_name
            )
        else:
            return overlay.create_slide(
                background_path=background_path,
                output_path=output_path,
                title=slide.get('display_text', slide.get('person_name', '')),
                subtitle=slide.get('subtitle'),
                slide_number=slide.get('slide_number'),
                style=visual_style,
                font_style=font_style,
                font_name=font_name
            )
    
    def create(self, topic: str, skip_image_generation: bool = False) -> Dict:
        """
        Create a complete TikTok slideshow from a topic.
        
        Args:
            topic: The slideshow topic (e.g., "6 philosophical practices for inner peace")
            skip_image_generation: If True, uses solid backgrounds (faster for testing)
        
        Returns:
            Dictionary with:
            - script: The generated slideshow script
            - slides: List of slide data
            - background_paths: Paths to background images
            - image_paths: Paths to final slides with text burned in
        """
        print(f"\n🎴 Creating TikTok Slideshow: {topic}")
        print("=" * 60)
        
        # Step 1: Generate script
        print("\n📝 Step 1: Generating script...")
        script = self._generate_script(topic)
        
        if not script:
            return {'script': None, 'slides': [], 'background_paths': [], 'image_paths': []}
        
        slides = script.get('slides', [])
        title = script.get('title', topic)
        
        # Safe name for files
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]
        
        # Step 2: Generate background images
        print(f"\n🎨 Step 2: Generating {len(slides)} background images...")
        background_paths = []
        
        for i, slide in enumerate(slides):
            if skip_image_generation:
                # Use solid background for testing
                bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{i}.png")
                self._create_fallback_background(bg_path)
                background_paths.append(bg_path)
            else:
                bg_path = self._generate_background(slide, safe_name, i)
                if bg_path:
                    background_paths.append(bg_path)
                else:
                    # Fallback to solid background
                    fallback_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{i}.png")
                    self._create_fallback_background(fallback_path)
                    background_paths.append(fallback_path)
        
        # Step 3: Burn text onto images
        print(f"\n📝 Step 3: Burning text onto slides...")
        image_paths = []
        
        for i, slide in enumerate(slides):
            bg_path = background_paths[i] if i < len(background_paths) else background_paths[-1]
            output_path = os.path.join(self.output_dir, f"{safe_name}_slide_{i}.png")
            
            final_path = self._burn_text_onto_slide(bg_path, slide, output_path)
            image_paths.append(final_path)
        
        # Save script for reference
        script_path = os.path.join(self.output_dir, f"{safe_name}_script.json")
        with open(script_path, 'w') as f:
            json.dump(script, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"✅ Slideshow complete!")
        print(f"   📊 Slides: {len(image_paths)}")
        print(f"   📁 Output: {self.output_dir}/")
        print(f"   📄 Script: {script_path}")
        
        return {
            'script': script,
            'slides': slides,
            'background_paths': background_paths,
            'image_paths': image_paths,
            'script_path': script_path
        }
    
    def create_from_script(self, script: Dict, skip_image_generation: bool = False) -> Dict:
        """
        Create slideshow from an existing script (skip script generation).
        
        Useful if you want to edit the script manually before generating images.
        
        Args:
            script: Slideshow script dictionary (can include 'font_style' and 'visual_style')
            skip_image_generation: Use solid backgrounds if True
        
        Returns:
            Same as create()
        """
        slides = script.get('slides', [])
        title = script.get('title', 'slideshow')
        
        # Get style settings from script (can be set by UI)
        font_name = script.get('font_name', None)  # Specific font: "inter", "playfair", "bebas", etc.
        font_style = script.get('font_style', None)  # Legacy: "bold", "italic", "elegant"
        visual_style = script.get('visual_style', 'modern')  # "modern", "elegant", "philosophaire"
        
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]
        
        print(f"\n🎴 Creating slideshow from script: {title}")
        print(f"   📊 Slides: {len(slides)}")
        print(f"   🎨 Font: {font_name or 'auto'}, Style: {visual_style}")
        
        # Generate backgrounds
        print(f"\n🎨 Generating {len(slides)} background images...")
        background_paths = []
        
        for i, slide in enumerate(slides):
            if skip_image_generation:
                bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{i}.png")
                self._create_fallback_background(bg_path)
                background_paths.append(bg_path)
            else:
                bg_path = self._generate_background(slide, safe_name, i)
                if bg_path:
                    background_paths.append(bg_path)
                else:
                    fallback_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{i}.png")
                    self._create_fallback_background(fallback_path)
                    background_paths.append(fallback_path)
        
        # Burn text with specified styles
        print(f"\n📝 Burning text onto slides...")
        image_paths = []
        
        for i, slide in enumerate(slides):
            bg_path = background_paths[i] if i < len(background_paths) else background_paths[-1]
            output_path = os.path.join(self.output_dir, f"{safe_name}_slide_{i}.png")
            
            final_path = self._burn_text_onto_slide(
                bg_path, slide, output_path,
                font_style=font_style,
                font_name=font_name,
                visual_style=visual_style
            )
            image_paths.append(final_path)
        
        print(f"\n✅ Created {len(image_paths)} slides")
        
        return {
            'script': script,
            'slides': slides,
            'background_paths': background_paths,
            'image_paths': image_paths
        }
    
    def preview_script(self, topic: str) -> Optional[Dict]:
        """
        Generate and preview a script without generating images.
        
        Useful for reviewing/editing the script before spending on image generation.
        
        Args:
            topic: The slideshow topic
        
        Returns:
            The generated script
        """
        print(f"\n📝 Generating script preview for: {topic}")
        script = self._generate_script(topic)
        
        if script:
            print("\n" + "=" * 60)
            print("📋 SCRIPT PREVIEW")
            print("=" * 60)
            print(f"Title: {script.get('title', 'Unknown')}")
            print(f"Total slides: {len(script.get('slides', []))}")
            print()
            
            for slide in script.get('slides', []):
                num = slide.get('slide_number', '?')
                stype = slide.get('slide_type', 'content')
                text = slide.get('display_text', '')
                subtitle = slide.get('subtitle', '')
                
                print(f"  [{num}] {stype.upper()}")
                print(f"      Text: {text}")
                if subtitle:
                    print(f"      Subtitle: {subtitle}")
                print()
            
            # Save for editing
            safe_name = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]
            script_path = os.path.join(self.output_dir, f"{safe_name}_script_preview.json")
            
            with open(script_path, 'w') as f:
                json.dump(script, f, indent=2)
            
            print(f"📄 Script saved to: {script_path}")
            print("   Edit this file, then use create_from_script() to generate images")
        
        return script
    
    def generate_single_slide(
        self,
        slide: Dict,
        slide_index: int,
        slideshow_title: str,
        skip_image_generation: bool = False,
        font_name: str = None,
        font_style: str = None,
        visual_style: str = "modern"
    ) -> Dict:
        """
        Generate a single slide (background + text overlay).
        
        This allows generating slides one at a time for better control.
        
        Args:
            slide: The slide data dictionary
            slide_index: Index of this slide (0, 1, 2, ...)
            slideshow_title: Title for file naming
            skip_image_generation: Use solid background if True
            font_name: Specific font to use
            font_style: Font style ("bold", "italic", etc.)
            visual_style: Visual style ("modern", "elegant", etc.)
        
        Returns:
            Dictionary with:
            - background_path: Path to background image
            - image_path: Path to final slide with text
            - success: Boolean indicating success
        """
        # Safe name for files
        safe_name = "".join(c for c in slideshow_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]
        
        print(f"\n🎴 Generating slide {slide_index}...")
        
        # Step 1: Generate or create background
        if skip_image_generation:
            bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{slide_index}.png")
            self._create_fallback_background(bg_path)
            print(f"   📷 Created fallback background")
        else:
            bg_path = self._generate_background(slide, safe_name, slide_index)
            if not bg_path:
                # Fallback to solid background
                bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{slide_index}.png")
                self._create_fallback_background(bg_path)
                print(f"   📷 Used fallback background (AI generation failed)")
            else:
                print(f"   📷 Generated AI background")
        
        # Step 2: Burn text onto background
        output_path = os.path.join(self.output_dir, f"{safe_name}_slide_{slide_index}.png")
        
        final_path = self._burn_text_onto_slide(
            bg_path, slide, output_path,
            font_style=font_style,
            font_name=font_name,
            visual_style=visual_style
        )
        
        print(f"   ✅ Slide {slide_index} complete: {final_path}")
        
        return {
            'background_path': bg_path,
            'image_path': final_path,
            'slide_index': slide_index,
            'success': True
        }


# Convenience function
def create_slideshow(topic: str, image_generator: str = "fal") -> Dict:
    """
    Quick function to create a TikTok slideshow.
    
    Args:
        topic: Slideshow topic
        image_generator: "fal" or "openai"
    
    Returns:
        Result dictionary with script and image paths
    """
    generator = TikTokSlideshow(image_generator=image_generator)
    return generator.create(topic)


# Test
if __name__ == "__main__":
    print("🧪 Testing TikTok Slideshow Generator")
    print("=" * 60)
    
    # Test with solid backgrounds (no API calls for images)
    slideshow = TikTokSlideshow()
    
    # First, just preview the script
    topic = "6 philosophical practices successful people use daily to find inner peace"
    script = slideshow.preview_script(topic)
    
    if script:
        print("\n" + "=" * 60)
        print("Now creating slides with solid backgrounds (test mode)...")
        print("=" * 60)
        
        result = slideshow.create_from_script(script, skip_image_generation=True)
        
        if result['image_paths']:
            print(f"\n🎉 Success! Created {len(result['image_paths'])} slides:")
            for path in result['image_paths']:
                print(f"   - {path}")
