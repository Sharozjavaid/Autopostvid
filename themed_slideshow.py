#!/usr/bin/env python3
"""
Themed Slideshow Generator - Creates slideshows using pre-configured visual themes

This module integrates theme_config.py with the TikTok slideshow pipeline to:
1. Use dialed-in image prompts for consistent visual style
2. Apply theme-specific text overlay settings (font, colors)
3. Support automatic theme selection based on content type

Usage:
    from themed_slideshow import ThemedSlideshow
    
    # Create slideshow with specific theme
    slideshow = ThemedSlideshow(theme="golden_dust")
    result = slideshow.create("5 Stoic Philosophers You Should Know")
    
    # Auto-select theme based on content
    slideshow = ThemedSlideshow(theme="auto")
    result = slideshow.create("Marcus Aurelius: The Philosopher Emperor")
    
    # Generate sample slideshow for a theme
    result = slideshow.generate_sample("glitch_titans")
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Import theme configuration
from theme_config import (
    THEMES, Theme, get_theme, get_enabled_themes,
    ContentType, TextOverlayMode, PHILOSOPHER_SCENES,
    build_scene_prompt, get_philosopher_scene
)


class ThemedSlideshow:
    """
    Themed slideshow generator that uses pre-configured visual themes.
    
    Each theme has:
    - Dialed-in image generation prompts (hook, content, outro)
    - Font and text styling configuration
    - Content type compatibility
    """
    
    def __init__(
        self,
        theme: str = "golden_dust",  # Theme ID or "auto"
        output_dir: str = "generated_slideshows",
        fal_model: str = None  # Override model from theme config
    ):
        """
        Initialize themed slideshow generator.
        
        Args:
            theme: Theme ID ("golden_dust", "glitch_titans", "oil_contrast", "scene_portrait")
                   or "auto" for automatic selection based on content
            output_dir: Output directory for generated slides
            fal_model: Optional model override (defaults to theme's configured model)
        """
        self.theme_id = theme
        self.output_dir = output_dir
        self.backgrounds_dir = os.path.join(output_dir, "backgrounds")
        self.fal_model_override = fal_model
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.backgrounds_dir, exist_ok=True)
        
        # Load theme if not auto
        self.theme = None
        if theme != "auto":
            self.theme = get_theme(theme)
            if not self.theme:
                print(f"⚠️ Theme '{theme}' not found, using 'golden_dust'")
                self.theme = get_theme("golden_dust")
        
        print(f"🎴 ThemedSlideshow initialized")
        if self.theme:
            print(f"   🎨 Theme: {self.theme.name}")
            print(f"   📝 Font: {self.theme.text_config.font_name}")
            print(f"   🖼️  Model: {self.fal_model_override or self.theme.image_config.model}")
    
    def _select_theme_for_content(self, topic: str, slides: List[Dict] = None) -> Theme:
        """
        Auto-select the best theme based on content analysis.
        
        Args:
            topic: The slideshow topic
            slides: Optional list of slides for deeper analysis
        
        Returns:
            Best matching Theme
        """
        topic_lower = topic.lower()
        
        # Check for list-style content (multiple items)
        list_indicators = ["5 ", "6 ", "7 ", "10 ", "philosophers who", "minds that", 
                          "quotes", "lessons", "practices", "habits", "secrets"]
        is_list = any(ind in topic_lower for ind in list_indicators)
        
        # Check for transformation/contrast content
        contrast_indicators = ["true happiness", "before and after", "transformation",
                              "vs", "modern vs ancient", "struggle"]
        is_contrast = any(ind in topic_lower for ind in contrast_indicators)
        
        # Check for single-topic/biographical content
        single_indicators = ["marcus aurelius:", "epictetus:", "socrates:", "the story of",
                            "the life of", "biography", "who was"]
        is_single = any(ind in topic_lower for ind in single_indicators)
        
        # Select theme based on content type
        if is_contrast:
            return get_theme("oil_contrast")
        elif is_single:
            return get_theme("scene_portrait")
        elif is_list:
            # For lists, prefer golden_dust (clean) or glitch_titans (edgy)
            if any(word in topic_lower for word in ["edge", "dark", "destroy", "change everything"]):
                return get_theme("glitch_titans")
            else:
                return get_theme("golden_dust")
        else:
            # Default to golden_dust (most versatile)
            return get_theme("golden_dust")
    
    def _get_theme_prompt(self, slide: Dict, slide_type: str) -> str:
        """
        Get the themed image prompt for a slide.
        
        Replaces placeholders in theme prompts with actual content.
        """
        theme = self.theme
        image_config = theme.image_config
        
        # Select base prompt based on slide type
        if slide_type == "hook":
            base_prompt = image_config.hook_prompt
        elif slide_type == "outro":
            base_prompt = image_config.outro_prompt
        else:
            base_prompt = image_config.content_prompt
        
        # Replace placeholders
        person_name = slide.get('person_name', '')
        display_text = slide.get('display_text', '')
        visual_desc = slide.get('visual_description', '')
        subtitle = slide.get('subtitle', '')
        
        prompt = base_prompt
        
        # Standard replacements
        prompt = prompt.replace("[PHILOSOPHER_NAME]", person_name or display_text)
        prompt = prompt.replace("[SCENE_DESCRIPTION]", visual_desc or f"philosophical scene featuring {person_name or display_text}")
        
        # For scene_portrait theme, use detailed philosopher data
        if self.theme_id == "scene_portrait" and person_name:
            philosopher_key = person_name.lower().replace(" ", "_")
            philosopher = get_philosopher_scene(philosopher_key)
            
            if philosopher:
                prompt = prompt.replace("[PHILOSOPHER_DESCRIPTION]", philosopher.get("description", "wise philosopher"))
                prompt = prompt.replace("[CLOTHING]", philosopher.get("clothing", "ancient robes"))
                
                settings = philosopher.get("settings", ["ancient temple"])
                prompt = prompt.replace("[SETTING]", settings[0])
                prompt = prompt.replace("[ENVIRONMENT_DETAILS]", settings[0])
                
                poses = philosopher.get("poses", ["contemplating"])
                prompt = prompt.replace("[POSE]", poses[0])
                
                mood = philosopher.get("mood", "wise, contemplative")
                prompt = prompt.replace("[EMOTION/QUALITY]", mood)
                prompt = prompt.replace("[EMOTIONAL_TONE]", mood)
                prompt = prompt.replace("[DIRECTION]", "the side")
        
        # Clean up any remaining placeholders
        import re
        prompt = re.sub(r'\[[\w/]+\]', '', prompt)
        
        return prompt.strip()
    
    def _generate_background(self, prompt: str, output_path: str) -> Optional[str]:
        """Generate background image using fal.ai with theme's model."""
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
            
            # Determine model
            model = self.fal_model_override or (self.theme.image_config.model if self.theme else "gpt15")
            
            # Model configurations
            FAL_MODELS = {
                "gpt15": {
                    "id": "fal-ai/gpt-image-1.5",
                    "image_size": "1024x1536",
                    "extra_args": {"quality": "low", "background": "auto"}
                },
                "flux": {
                    "id": "fal-ai/flux/schnell",
                    "image_size": "portrait_16_9",
                    "extra_args": {"num_inference_steps": 4, "guidance_scale": 3.5}
                }
            }
            
            model_config = FAL_MODELS.get(model, FAL_MODELS["gpt15"])
            
            print(f"   🎨 Generating with {model}...")
            
            result = fal_client.subscribe(
                model_config["id"],
                arguments={
                    "prompt": prompt,
                    "image_size": model_config["image_size"],
                    "num_images": 1,
                    "output_format": "png",
                    **model_config.get("extra_args", {})
                },
            )
            
            images = result.get('images', [])
            if not images:
                print("   ❌ No images in response")
                return None
            
            image_url = images[0].get('url')
            if not image_url:
                return None
            
            # Handle base64 or URL
            if image_url.startswith('data:'):
                header, encoded_data = image_url.split(',', 1)
                image_bytes = base64.b64decode(encoded_data)
                img = Image.open(io.BytesIO(image_bytes))
            else:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
            
            # Resize to TikTok dimensions
            img = ImageOps.fit(img, (1080, 1920), method=Image.Resampling.LANCZOS)
            img.save(output_path, 'PNG')
            
            print(f"   ✅ Saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Image generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _burn_text_onto_slide(
        self,
        background_path: str,
        slide: Dict,
        output_path: str,
        slide_type: str = "content"
    ) -> str:
        """Apply themed text overlay to a slide."""
        from text_overlay import TextOverlay
        
        text_config = self.theme.text_config
        overlay = TextOverlay(default_style="social")
        
        # Get theme's font and style
        font_name = text_config.font_name
        
        # Determine visual style based on theme
        visual_style = "modern"
        if self.theme_id == "oil_contrast":
            visual_style = "elegant"
        elif self.theme_id == "scene_portrait":
            visual_style = "modern"
        elif self.theme_id == "glitch_titans":
            visual_style = "bold"
        
        if slide_type == 'hook':
            return overlay.create_hook_slide(
                background_path=background_path,
                output_path=output_path,
                hook_text=slide.get('display_text', ''),
                style=visual_style,
                font_name=font_name
            )
        elif slide_type == 'outro':
            return overlay.create_outro_slide(
                background_path=background_path,
                output_path=output_path,
                text=slide.get('display_text', ''),
                subtitle=slide.get('subtitle'),
                style=visual_style,
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
                font_name=font_name
            )
    
    def create(self, topic: str) -> Dict:
        """
        Create a complete themed slideshow from a topic.
        
        Args:
            topic: The slideshow topic
        
        Returns:
            Dictionary with script, slides, and image paths
        """
        print(f"\n🎴 Creating Themed Slideshow: {topic}")
        print("=" * 60)
        
        # Auto-select theme if needed
        if self.theme_id == "auto" or not self.theme:
            self.theme = self._select_theme_for_content(topic)
            print(f"   🎨 Auto-selected theme: {self.theme.name}")
        
        # Step 1: Generate script
        print("\n📝 Step 1: Generating script...")
        from gemini_handler import GeminiHandler
        gemini = GeminiHandler()
        script = gemini.generate_slideshow_script(topic)
        
        if not script:
            print("   ❌ Failed to generate script")
            return {'script': None, 'slides': [], 'image_paths': []}
        
        slides = script.get('slides', [])
        title = script.get('title', topic)
        
        print(f"   ✅ Script generated: {title}")
        print(f"   📊 Slides: {len(slides)}")
        
        # Safe name for files
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]
        
        # Step 2: Generate themed background images
        print(f"\n🎨 Step 2: Generating {len(slides)} themed backgrounds...")
        background_paths = []
        
        for i, slide in enumerate(slides):
            slide_type = slide.get('slide_type', 'content')
            prompt = self._get_theme_prompt(slide, slide_type)
            
            bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_bg_{i}.png")
            result = self._generate_background(prompt, bg_path)
            
            if result:
                background_paths.append(result)
            else:
                # Create fallback
                from text_overlay import TextOverlay
                overlay = TextOverlay()
                overlay.create_solid_background(bg_path, color=(20, 25, 35), gradient=True)
                background_paths.append(bg_path)
        
        # Step 3: Apply themed text overlay
        print(f"\n📝 Step 3: Applying themed text overlay...")
        image_paths = []
        
        for i, slide in enumerate(slides):
            slide_type = slide.get('slide_type', 'content')
            bg_path = background_paths[i] if i < len(background_paths) else background_paths[-1]
            output_path = os.path.join(self.output_dir, f"{safe_name}_slide_{i}.png")
            
            final_path = self._burn_text_onto_slide(bg_path, slide, output_path, slide_type)
            image_paths.append(final_path)
        
        # Save script
        script_path = os.path.join(self.output_dir, f"{safe_name}_script.json")
        script['theme'] = self.theme_id
        script['theme_name'] = self.theme.name
        with open(script_path, 'w') as f:
            json.dump(script, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"✅ Themed slideshow complete!")
        print(f"   🎨 Theme: {self.theme.name}")
        print(f"   📊 Slides: {len(image_paths)}")
        print(f"   📁 Output: {self.output_dir}/")
        
        return {
            'script': script,
            'slides': slides,
            'background_paths': background_paths,
            'image_paths': image_paths,
            'theme': self.theme_id,
            'theme_name': self.theme.name
        }
    
    def generate_sample(self, theme_id: str = None) -> Dict:
        """
        Generate a sample slideshow to preview a theme.
        
        Creates a small 3-slide sample (hook, content, outro) using
        the theme's example topics and prompts.
        
        Args:
            theme_id: Theme to sample (uses current theme if not specified)
        
        Returns:
            Dictionary with sample slide paths and metadata
        """
        if theme_id:
            self.theme = get_theme(theme_id)
            self.theme_id = theme_id
        
        if not self.theme:
            self.theme = get_theme("golden_dust")
            self.theme_id = "golden_dust"
        
        print(f"\n🎴 Generating Sample for Theme: {self.theme.name}")
        print("=" * 60)
        
        # Use example topics from theme
        example_topic = self.theme.example_topics[0] if self.theme.example_topics else "5 Philosophers You Should Know"
        
        # Create sample slides (hook, content, outro)
        sample_slides = [
            {
                'slide_type': 'hook',
                'display_text': 'THEY CHANGED EVERYTHING',
                'subtitle': '5 minds that shaped reality',
                'visual_description': ''
            },
            {
                'slide_type': 'person',
                'slide_number': 2,
                'display_text': 'MARCUS AURELIUS',
                'person_name': 'Marcus Aurelius',
                'subtitle': 'Born a slave. Died a legend.',
                'visual_description': ''
            },
            {
                'slide_type': 'outro',
                'display_text': 'CHOOSE YOUR PATH',
                'subtitle': 'Follow for more ancient wisdom',
                'visual_description': ''
            }
        ]
        
        safe_name = f"sample_{self.theme_id}"
        
        print(f"\n🎨 Generating 3 sample slides...")
        background_paths = []
        image_paths = []
        
        for i, slide in enumerate(sample_slides):
            slide_type = slide.get('slide_type', 'content')
            
            # Generate themed background
            prompt = self._get_theme_prompt(slide, slide_type)
            bg_path = os.path.join(self.backgrounds_dir, f"{safe_name}_{slide_type}_bg.png")
            
            print(f"\n[{i+1}/3] Generating {slide_type.upper()} slide...")
            result = self._generate_background(prompt, bg_path)
            
            if result:
                background_paths.append(result)
            else:
                from text_overlay import TextOverlay
                overlay = TextOverlay()
                overlay.create_solid_background(bg_path, color=(20, 25, 35), gradient=True)
                background_paths.append(bg_path)
            
            # Apply text overlay
            output_path = os.path.join(self.output_dir, f"{safe_name}_{slide_type}.png")
            final_path = self._burn_text_onto_slide(background_paths[-1], slide, output_path, slide_type)
            image_paths.append(final_path)
        
        print("\n" + "=" * 60)
        print(f"✅ Sample generated!")
        print(f"   🎨 Theme: {self.theme.name}")
        print(f"   📊 Slides: {len(image_paths)}")
        for path in image_paths:
            print(f"   📄 {path}")
        
        return {
            'theme': self.theme_id,
            'theme_name': self.theme.name,
            'sample_slides': sample_slides,
            'background_paths': background_paths,
            'image_paths': image_paths,
            'example_topic': example_topic
        }


def get_available_themes() -> Dict[str, Dict]:
    """
    Get all available themes with their metadata.
    
    Returns:
        Dictionary of theme_id -> theme info
    """
    themes = {}
    for theme_id, theme in get_enabled_themes().items():
        themes[theme_id] = {
            'id': theme_id,
            'name': theme.name,
            'description': theme.description,
            'content_types': [ct.value for ct in theme.content_types],
            'font': theme.text_config.font_name,
            'model': theme.image_config.model,
            'example_topics': theme.example_topics[:3]
        }
    return themes


# Convenience functions
def create_themed_slideshow(topic: str, theme: str = "golden_dust") -> Dict:
    """Quick function to create a themed slideshow."""
    gen = ThemedSlideshow(theme=theme)
    return gen.create(topic)


def generate_theme_sample(theme_id: str) -> Dict:
    """Quick function to generate a theme sample."""
    gen = ThemedSlideshow(theme=theme_id)
    return gen.generate_sample()


if __name__ == "__main__":
    print("=" * 60)
    print("THEMED SLIDESHOW GENERATOR")
    print("=" * 60)
    
    # List available themes
    print("\n📋 Available Themes:")
    for theme_id, info in get_available_themes().items():
        print(f"\n  [{theme_id}] {info['name']}")
        print(f"     {info['description'][:60]}...")
        print(f"     Font: {info['font']}, Model: {info['model']}")
    
    # Generate a sample
    print("\n" + "=" * 60)
    print("Generating sample slideshow...")
    print("=" * 60)
    
    result = generate_theme_sample("golden_dust")
    
    if result['image_paths']:
        print(f"\n🎉 Sample generated successfully!")
        for path in result['image_paths']:
            print(f"   📄 {path}")
