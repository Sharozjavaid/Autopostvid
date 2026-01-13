#!/usr/bin/env python3
"""
Template-Based Image Generator

Uses visual templates to generate consistent images across slideshows.
- Lock in a visual style (template)
- Apply it to all slides in a batch
- Uses OpenAI GPT-Image-1 via fal.ai (cheaper than Nano)

Templates define:
- Base aesthetic (colors, lighting, style)
- How to incorporate text
- How to handle different slide types (hook, person, lesson, outro)
"""

import os
import fal_client
import requests
from PIL import Image, ImageOps
import io
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════════
# VISUAL TEMPLATES
# ═══════════════════════════════════════════════════════════════════
# Each template is a self-contained visual style that can be applied
# to any slideshow. The template defines:
# - Style (colors, lighting, aesthetic)
# - How to handle text overlays
# - Slide-type-specific variations

TEMPLATES = {
    # ───────────────────────────────────────────────────────────────
    # TEMPLATE 1: Classical Renaissance (Dark & Moody)
    # ───────────────────────────────────────────────────────────────
    "classical_renaissance": {
        "name": "Classical Renaissance",
        "description": "Dark oil painting style with Caravaggio lighting. Gold accents, marble textures.",
        "base_style": """Dark moody classical oil painting style, dramatic Caravaggio chiaroscuro lighting, 
Renaissance/Baroque aesthetic, rich deep colors (burgundy, gold, deep blue), 
mysterious shadows with golden highlights, warm candlelight atmosphere, 
oil on canvas texture, museum-quality fine art.""",
        
        "text_style": """Bold text overlay prominently displaying: "[TEXT]"
The text should be large, centered, golden/yellow metallic with slight 3D emboss effect,
cinematic movie poster typography, highly legible against the dark background.
Classical serif font with ornate styling.""",
        
        "slide_types": {
            "hook": {
                "visual": "Epic dramatic scene, silhouettes of multiple figures, golden light rays breaking through darkness",
                "text_position": "center"
            },
            "person": {
                "visual": "[PERSON_NAME] as a classical marble statue or oil portrait, dramatic side lighting, aged patina",
                "text_position": "lower_center"
            },
            "lesson": {
                "visual": "Symbolic still life representing the concept - ancient scrolls, candles, philosophical objects",
                "text_position": "center"
            },
            "outro": {
                "visual": "Inspiring upward-looking composition, light breaking through, sense of revelation",
                "text_position": "center"
            }
        },
        "color_palette": ["#1a1a2e", "#16213e", "#e94560", "#d4af37", "#2c1810"],
        "best_for": ["Philosophy", "Historical figures", "Ancient wisdom"]
    },
    
    # ───────────────────────────────────────────────────────────────
    # TEMPLATE 2: Stoic Marble (Minimalist)
    # ───────────────────────────────────────────────────────────────
    "stoic_marble": {
        "name": "Stoic Marble",
        "description": "Clean white marble statues on pure black backgrounds. Powerful and minimal.",
        "base_style": """Stunning white marble sculpture against pure black background,
dramatic side lighting creates strong shadows, photorealistic marble texture with subtle veins,
Greek/Roman sculptural style, museum-quality presentation, 
ultra high detail, minimalist powerful composition.""",
        
        "text_style": """Clean white sans-serif text overlay: "[TEXT]"
Bold, modern typography like TikTok/Instagram captions,
subtle drop shadow for legibility, centered composition,
professional social media aesthetic.""",
        
        "slide_types": {
            "hook": {
                "visual": "Multiple marble busts arranged dramatically, stark contrast, powerful composition",
                "text_position": "center"
            },
            "person": {
                "visual": "Single marble bust of [PERSON_NAME], noble expression, perfect sculptural detail",
                "text_position": "lower_center"
            },
            "lesson": {
                "visual": "Abstract marble form suggesting the concept - hands, eyes, or symbolic gesture",
                "text_position": "center"
            },
            "outro": {
                "visual": "Single powerful marble figure looking upward, aspirational pose",
                "text_position": "center"
            }
        },
        "color_palette": ["#000000", "#ffffff", "#d4d4d4", "#8c8c8c"],
        "best_for": ["Stoic content", "Quotes", "Minimalist aesthetic"]
    },
    
    # ───────────────────────────────────────────────────────────────
    # TEMPLATE 3: Dark Academia (Library Aesthetic)
    # ───────────────────────────────────────────────────────────────
    "dark_academia": {
        "name": "Dark Academia",
        "description": "Moody library aesthetic with books, candles, warm wood tones.",
        "base_style": """Dark academia aesthetic, moody ancient library setting,
towering bookshelves with leather-bound volumes, warm candlelight dancing,
rich mahogany wood and worn leather textures, scattered papers with handwritten notes,
dust motes floating in beams of warm light, atmospheric and contemplative,
color palette of deep browns, burgundy, forest green, aged gold,
cinematic photography style.""",
        
        "text_style": """Elegant serif text overlay: "[TEXT]"
Warm cream/gold color, sophisticated typography like book titles,
subtle glow effect, positioned for maximum readability,
literary aesthetic matching the scene.""",
        
        "slide_types": {
            "hook": {
                "visual": "Grand library hall with dramatic lighting, rows of ancient books fading into shadows",
                "text_position": "center"
            },
            "person": {
                "visual": "Scholar's desk with open book, candle, and portrait silhouette suggesting [PERSON_NAME]",
                "text_position": "lower_center"
            },
            "lesson": {
                "visual": "Open book with dramatic lighting, quill and ink, contemplative still life",
                "text_position": "center"
            },
            "outro": {
                "visual": "Light streaming through library window, sense of enlightenment and possibility",
                "text_position": "center"
            }
        },
        "color_palette": ["#1a1612", "#2c2418", "#8b4513", "#daa520", "#2f4f4f"],
        "best_for": ["Book quotes", "Literary philosophy", "Modern audience appeal"]
    },
    
    # ───────────────────────────────────────────────────────────────
    # TEMPLATE 4: Cosmic Wisdom (Surreal/Spiritual)
    # ───────────────────────────────────────────────────────────────
    "cosmic_wisdom": {
        "name": "Cosmic Wisdom",
        "description": "Philosophers against cosmic nebula backgrounds. Blends ancient wisdom with infinite universe.",
        "base_style": """Surreal cosmic artwork, breathtaking nebula background,
swirling galaxies, stars, and cosmic dust in deep purple, blue, and gold hues,
ethereal lighting emanating from the cosmos, sense of infinite wisdom,
blend of classical and cosmic imagery, hyper-detailed, mystical atmosphere.""",
        
        "text_style": """Ethereal glowing text overlay: "[TEXT]"
White/gold gradient text with soft cosmic glow,
elegant sans-serif font, centered and prominent,
appears to float in the cosmic space.""",
        
        "slide_types": {
            "hook": {
                "visual": "Vast cosmic scene, silhouettes of wise figures against nebula, sacred geometry hints",
                "text_position": "center"
            },
            "person": {
                "visual": "Ethereal figure of [PERSON_NAME] merging with starlight, cosmic meditation pose",
                "text_position": "lower_center"
            },
            "lesson": {
                "visual": "Abstract cosmic symbol representing the concept, sacred geometry, floating in space",
                "text_position": "center"
            },
            "outro": {
                "visual": "Figure reaching toward brilliant cosmic light, transcendence and enlightenment",
                "text_position": "center"
            }
        },
        "color_palette": ["#0a0a1a", "#1a0a2e", "#4a00e0", "#8e2de2", "#ffd700"],
        "best_for": ["Existential philosophy", "Spiritual content", "Eastern philosophy"]
    },
    
}


class TemplateImageGenerator:
    """
    Generate images using visual templates via fal.ai.
    
    Usage:
        gen = TemplateImageGenerator()
        
        # List available templates
        gen.list_templates()
        
        # Generate a single slide
        path = gen.generate_slide(
            template_id="classical_renaissance",
            slide_data={"display_text": "MARCUS AURELIUS", "slide_type": "person"},
            slide_number=1,
            title="test"
        )
        
        # Generate all slides for a slideshow
        paths = gen.generate_slideshow(
            template_id="stoic_marble",
            slides=slides_data,
            title="5 Philosophers"
        )
    """
    
    def __init__(self, model: str = "gpt-image-1"):
        """
        Initialize the generator.
        
        Args:
            model: Which model to use via fal.ai
                - "gpt-image-1" (default) - OpenAI GPT Image 1
                - "gpt-image-1.5" - OpenAI GPT Image 1.5 (faster)
                - "flux-schnell" - Flux Schnell (fastest/cheapest for backgrounds)
        """
        self.api_key = os.getenv('FAL_KEY')
        if not self.api_key:
            raise ValueError("FAL_KEY not found. Set it in .env file")
        
        os.environ['FAL_KEY'] = self.api_key
        
        self.model = model
        self.model_id = self._get_model_id(model)
        self.output_dir = "generated_slideshows"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ TemplateImageGenerator initialized")
        print(f"   Model: {model} ({self.model_id})")
        print(f"   Templates: {len(TEMPLATES)}")
    
    def _get_model_id(self, model: str) -> str:
        """Get fal.ai model ID from model name"""
        model_map = {
            "gpt-image-1": "fal-ai/gpt-image-1/text-to-image",
            "gpt-image-1.5": "fal-ai/gpt-image-1.5",
            "flux-schnell": "fal-ai/flux/schnell"
        }
        return model_map.get(model, "fal-ai/gpt-image-1/text-to-image")
    
    def list_templates(self) -> Dict:
        """List all available templates"""
        print("\n📋 Available Templates:")
        print("=" * 50)
        
        for tid, template in TEMPLATES.items():
            print(f"\n🎨 {template['name']} ({tid})")
            print(f"   {template['description']}")
            print(f"   Best for: {', '.join(template['best_for'])}")
        
        return TEMPLATES
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        return TEMPLATES.get(template_id)
    
    def _build_prompt(
        self,
        template: Dict,
        slide_data: Dict,
        include_text: bool = True
    ) -> str:
        """
        Build the full prompt for a slide using the template.
        
        Args:
            template: The template dict
            slide_data: Slide data with display_text, slide_type, person_name, etc.
            include_text: Whether to include text in the image (or generate bg only)
        """
        slide_type = slide_data.get('slide_type', 'lesson')
        display_text = slide_data.get('display_text', '')
        person_name = slide_data.get('person_name', '')
        visual_override = slide_data.get('visual_description', '')
        
        # Get slide-type-specific visual
        slide_type_config = template.get('slide_types', {}).get(slide_type, {})
        type_visual = slide_type_config.get('visual', '')
        
        # Replace person name placeholder
        if person_name and '[PERSON_NAME]' in type_visual:
            type_visual = type_visual.replace('[PERSON_NAME]', person_name)
        elif '[PERSON_NAME]' in type_visual:
            type_visual = type_visual.replace('[PERSON_NAME]', display_text)
        
        # Use override if provided, otherwise use template default
        visual_description = visual_override if visual_override else type_visual
        
        # Build full prompt
        parts = [
            template['base_style'],
            visual_description
        ]
        
        # Add text style if including text in image
        if include_text and display_text:
            text_style = template['text_style'].replace('[TEXT]', display_text.upper())
            parts.append(text_style)
        
        # Add format requirements
        parts.append("Vertical 9:16 aspect ratio, mobile format, no watermarks or logos.")
        
        return "\n\n".join(parts)
    
    def generate_slide(
        self,
        template_id: str,
        slide_data: Dict,
        slide_number: int,
        title: str,
        include_text: bool = True
    ) -> Optional[str]:
        """
        Generate a single slide image.
        
        Args:
            template_id: Which template to use
            slide_data: Slide data dict with display_text, slide_type, etc.
            slide_number: Slide number for filename
            title: Slideshow title for filename
            include_text: Whether to burn text into image
            
        Returns:
            Path to saved image, or None on failure
        """
        template = self.get_template(template_id)
        if not template:
            print(f"❌ Template not found: {template_id}")
            return None
        
        prompt = self._build_prompt(template, slide_data, include_text)
        
        print(f"\n🎨 Generating slide {slide_number}...")
        print(f"   Template: {template['name']}")
        print(f"   Type: {slide_data.get('slide_type', 'unknown')}")
        print(f"   Text: {slide_data.get('display_text', '')[:30]}...")
        
        try:
            # Build arguments based on model
            if "flux" in self.model_id:
                # Flux uses different params
                arguments = {
                    "prompt": prompt,
                    "image_size": {
                        "width": 768,
                        "height": 1344
                    },
                    "num_images": 1
                }
            else:
                # GPT Image models
                arguments = {
                    "prompt": prompt,
                    "image_size": "1024x1536",  # Vertical
                    "quality": "low",  # Fast/cheap
                    "num_images": 1,
                    "output_format": "png"
                }
            
            result = fal_client.subscribe(
                self.model_id,
                arguments=arguments
            )
            
            # Extract image
            images = result.get('images', [])
            if not images:
                print(f"   ❌ No images in response")
                return None
            
            image_url = images[0].get('url')
            if not image_url:
                print(f"   ❌ No URL in response")
                return None
            
            # Download and process
            if image_url.startswith('data:'):
                # Base64 data URI
                import base64
                header, encoded = image_url.split(',', 1)
                image_bytes = base64.b64decode(encoded)
                image = Image.open(io.BytesIO(image_bytes))
            else:
                # HTTP URL
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            
            # Resize to exact TikTok dimensions
            image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
            
            # Save
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:40]
            filename = f"{self.output_dir}/{safe_title}_slide_{slide_number}.png"
            image.save(filename, 'PNG')
            
            print(f"   ✅ Saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_slideshow(
        self,
        template_id: str,
        slides: List[Dict],
        title: str,
        include_text: bool = True,
        progress_callback=None
    ) -> List[str]:
        """
        Generate all slides for a slideshow using the same template.
        
        Args:
            template_id: Template to use for all slides
            slides: List of slide data dicts
            title: Slideshow title for filenames
            include_text: Whether to burn text into images
            progress_callback: Optional callback(current, total, status)
            
        Returns:
            List of paths to generated images
        """
        template = self.get_template(template_id)
        if not template:
            print(f"❌ Template not found: {template_id}")
            return []
        
        print(f"\n🎬 Generating slideshow with template: {template['name']}")
        print(f"   Slides: {len(slides)}")
        print(f"   Include text: {include_text}")
        
        image_paths = []
        
        for i, slide in enumerate(slides):
            if progress_callback:
                progress_callback(i + 1, len(slides), f"Generating slide {i + 1}")
            
            path = self.generate_slide(
                template_id=template_id,
                slide_data=slide,
                slide_number=i,
                title=title,
                include_text=include_text
            )
            
            if path:
                image_paths.append(path)
        
        print(f"\n✅ Generated {len(image_paths)}/{len(slides)} slides")
        return image_paths
    
    def preview_template(self, template_id: str) -> Optional[str]:
        """
        Generate a single preview image for a template.
        Uses example content to show the template's style.
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Example slide for preview
        example_slide = {
            "display_text": "THEY CHANGED EVERYTHING",
            "slide_type": "hook",
            "person_name": None,
            "visual_description": None
        }
        
        return self.generate_slide(
            template_id=template_id,
            slide_data=example_slide,
            slide_number=0,
            title=f"preview_{template_id}",
            include_text=True
        )


def test_template_generator():
    """Test the template-based generator"""
    
    print("\n" + "=" * 60)
    print("TESTING TEMPLATE IMAGE GENERATOR")
    print("=" * 60)
    
    # Check for FAL_KEY
    if not os.getenv('FAL_KEY'):
        print("❌ FAL_KEY not found. Please set it in .env")
        return
    
    gen = TemplateImageGenerator(model="gpt-image-1")
    
    # List templates
    gen.list_templates()
    
    # Test with one template and one slide
    print("\n" + "=" * 60)
    print("GENERATING TEST SLIDE")
    print("=" * 60)
    
    test_slide = {
        "display_text": "MARCUS AURELIUS",
        "slide_type": "person",
        "person_name": "Marcus Aurelius",
        "subtitle": "He ruled Rome. Every night he asked: 'Was I good today?'"
    }
    
    path = gen.generate_slide(
        template_id="classical_renaissance",
        slide_data=test_slide,
        slide_number=1,
        title="template_test"
    )
    
    if path:
        print(f"\n🎉 Test successful! Image saved to: {path}")
    else:
        print("\n❌ Test failed")


if __name__ == "__main__":
    test_template_generator()
