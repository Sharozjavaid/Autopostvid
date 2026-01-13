
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

# ============================================================================
# FEATURE FLAGS - Control which image generation methods are active
# ============================================================================
# Set to False to disable Gemini 3 Pro image generation (saves money)
ENABLE_GEMINI_IMAGE_GENERATION = False  # PAUSED - too expensive

# Set to True to use fal.ai for backgrounds (cheaper)
ENABLE_FAL_BACKGROUNDS = True  # ACTIVE - cost-effective

# Which fal.ai model to use: "flux" (Flux Schnell 1.1) or "gpt15" (GPT Image 1.5)
FAL_MODEL = "gpt15"  # "gpt15" = detailed, high quality (recommended)

# Set to True to use programmatic text overlay (Pillow) instead of AI-burned text
USE_PROGRAMMATIC_TEXT_OVERLAY = True  # ACTIVE - consistent, free
# ============================================================================

# fal.ai model configurations
FAL_MODELS = {
    "gpt15": {
        "id": "fal-ai/gpt-image-1.5",
        "name": "GPT Image 1.5",
        "image_size": "1024x1536",
        "extra_args": {"quality": "low", "background": "auto"}
    },
    "flux": {
        "id": "fal-ai/flux/schnell",
        "name": "Flux Schnell 1.1",
        "image_size": "portrait_16_9",  # Correct format for Flux API
        "extra_args": {
            "num_inference_steps": 4,
            "guidance_scale": 3.5,
            "enable_safety_checker": True
        }
    }
}


class SmartImageGenerator:
    def __init__(self):
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Gemini client (only if enabled)
        self.client = None
        self.image_model_name = 'gemini-3-pro-image-preview'
        
        if ENABLE_GEMINI_IMAGE_GENERATION:
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                self.client = genai.Client(api_key=api_key)
                print("✅ Gemini 3 Pro Image generation ENABLED")
            else:
                print("⚠️ GOOGLE_API_KEY not found - Gemini disabled")
        else:
            print("💤 Gemini 3 Pro Image generation PAUSED (cost savings mode)")
        
        # Initialize fal.ai generator (if enabled)
        self.fal_available = False
        if ENABLE_FAL_BACKGROUNDS:
            fal_key = os.getenv('FAL_KEY')
            if fal_key:
                self.fal_available = True
                model_info = FAL_MODELS.get(FAL_MODEL, FAL_MODELS["flux"])
                print(f"✅ fal.ai {model_info['name']} ENABLED (cost-effective backgrounds)")
            else:
                print("⚠️ FAL_KEY not found - fal.ai disabled")
        
        # Initialize text overlay (if enabled)
        self.text_overlay = None
        if USE_PROGRAMMATIC_TEXT_OVERLAY:
            try:
                from text_overlay import TextOverlay
                self.text_overlay = TextOverlay()
                print("✅ Programmatic text overlay ENABLED (Pillow)")
            except ImportError:
                print("⚠️ text_overlay not available")
        
        # Legacy text style (kept for reference, but not used when text overlay is active)
        self.text_style = """bold golden/yellow metallic text with slight 3D emboss effect, 
            dramatic lighting, dark moody background, text centered in frame, 
            cinematic typography like movie poster, high contrast, 
            Renaissance/Baroque oil painting aesthetic"""
    
    def _build_text_overlay(self, scene_data: dict, scene_number: int) -> str:
        """Build appropriate text overlay based on scene data.
        
        For list-style content:
        - Hook scene (list_item=0, scene 1): Use hook text or "THEY CHANGED EVERYTHING" style
        - Person/Item scenes: "#1 SOCRATES", "#2 CONFUCIUS", etc.
        - Quote scenes: The key quote text
        - Outro: "PICK YOUR MENTOR" or call-to-action
        
        For narrative content:
        - Use key_concept as the overlay text
        """
        list_item = scene_data.get('list_item', 0)
        key_concept = scene_data.get('key_concept', '')
        display_text = scene_data.get('display_text', '')
        slide_type = scene_data.get('slide_type', '')
        person_name = scene_data.get('person_name', '')
        visual_desc = scene_data.get('visual_description', '')
        
        # Check if visual_description already has text overlay specified
        if "text overlay:" in visual_desc.lower():
            # Extract the text overlay from visual description
            import re
            match = re.search(r"text overlay[:\s]+['\"]?([^'\"\.]+)['\"]?", visual_desc, re.IGNORECASE)
            if match:
                return match.group(1).strip().upper()
        
        # For slideshow-style content
        if display_text:
            return display_text.upper()
        
        # For list-style content
        if list_item is not None:
            if list_item == 0:
                # Hook or outro scene
                if scene_number == 1:
                    # First scene - hook
                    if 'hook' in key_concept.lower():
                        return "THEY CHANGED EVERYTHING"
                    return key_concept.upper() if key_concept else "THE TRUTH REVEALED"
                else:
                    # Outro scene
                    if 'outro' in key_concept.lower():
                        return "PICK YOUR PATH"
                    return key_concept.upper() if key_concept else "YOUR CHOICE"
            else:
                # List item scene
                if person_name:
                    return f"#{list_item} {person_name.upper()}"
                elif key_concept and 'quote' not in key_concept.lower():
                    return f"#{list_item} {key_concept.upper()}"
                elif key_concept:
                    # Quote scene - just show the concept
                    return key_concept.upper()
        
        # For narrative content, use key concept
        if key_concept:
            return key_concept.upper()
        
        # Fallback
        return f"SCENE {scene_number}"
    
    def _add_text_overlay_to_prompt(self, base_prompt: str, text_overlay: str) -> str:
        """Add text overlay instructions to the image generation prompt.
        
        This ensures the AI generates the text as part of the image with
        consistent styling (gold metallic, dramatic, centered).
        """
        text_instruction = f"""
CRITICAL TEXT REQUIREMENT: The image MUST prominently display the text "{text_overlay}" 
as large, bold, golden/yellow metallic lettering with a subtle 3D emboss effect.
The text should be centered in the frame, highly legible, with dramatic cinematic typography 
like a movie poster title. Use high contrast against the dark background.
The text style should match Renaissance/Baroque aesthetics with ornate, classical font styling.
"""
        
        # Combine with base prompt
        enhanced_prompt = f"{text_instruction}\n\nScene visual: {base_prompt}"
        
        return enhanced_prompt
    
    def generate_image_with_nano(
        self, 
        prompt: str, 
        scene_number: int, 
        story_title: str, 
        prompt_override: str = None,
        text_overlay: str = None,
        scene_data: dict = None
    ) -> str:
        """Generate image for a scene - routes to the active image generator.
        
        Current routing (based on feature flags):
        1. If ENABLE_FAL_GPT15_BACKGROUNDS + USE_PROGRAMMATIC_TEXT_OVERLAY:
           → Generate background with fal.ai GPT 1.5, then burn text with Pillow
        2. If ENABLE_GEMINI_IMAGE_GENERATION:
           → Use Gemini 3 Pro Image (legacy, expensive)
        3. Fallback:
           → Create enhanced placeholder
        
        Args:
            prompt: Visual description for the scene
            scene_number: Scene number (1-indexed)
            story_title: Title of the story
            prompt_override: Optional full prompt override
            text_overlay: Text to embed in the image
            scene_data: Full scene dict with list_item, key_concept, display_text, etc.
        """
        
        # Build text overlay if not explicitly provided
        if not text_overlay and scene_data:
            text_overlay = self._build_text_overlay(scene_data, scene_number)
        
        # Use override if provided, otherwise use the visual description
        final_prompt = prompt_override if prompt_override else prompt
        
        # Safe title for filenames
        safe_title = story_title.replace(' ', '_')
        
        # =================================================================
        # ROUTE 1: fal.ai + Programmatic Text Overlay (PREFERRED)
        # =================================================================
        if ENABLE_FAL_BACKGROUNDS and self.fal_available and USE_PROGRAMMATIC_TEXT_OVERLAY and self.text_overlay:
            print(f"🎨 Using fal.ai GPT 1.5 + Text Overlay (cost-effective mode)")
            return self._generate_with_fal_and_overlay(
                prompt=final_prompt,
                scene_number=scene_number,
                story_title=story_title,
                text_overlay=text_overlay,
                scene_data=scene_data
            )
        
        # =================================================================
        # ROUTE 2: Gemini 3 Pro Image (LEGACY - expensive, PAUSED by default)
        # =================================================================
        if ENABLE_GEMINI_IMAGE_GENERATION and self.client:
            print(f"🎨 Using Gemini 3 Pro Image (legacy mode - expensive)")
            return self._generate_with_gemini(
                prompt=final_prompt,
                scene_number=scene_number,
                story_title=story_title,
                text_overlay=text_overlay
            )
        
        # =================================================================
        # ROUTE 3: Fallback to placeholder
        # =================================================================
        print(f"⚠️ No image generator available, creating placeholder...")
        return self.create_enhanced_placeholder(final_prompt, scene_number, story_title)
    
    def _generate_with_fal_and_overlay(
        self,
        prompt: str,
        scene_number: int,
        story_title: str,
        text_overlay: str = None,
        scene_data: dict = None
    ) -> str:
        """Generate background with fal.ai, then burn text with Pillow.
        
        This is the cost-effective approach:
        1. Generate a background-only image (no text in AI prompt)
        2. Use Pillow to add clean, consistent text overlay
        
        Supports: Flux Schnell 1.1 or GPT Image 1.5 (based on FAL_MODEL setting)
        """
        safe_title = story_title.replace(' ', '_')
        
        # Build background-only prompt (NO text instructions)
        background_prompt = self._build_background_prompt(prompt)
        
        # Get model config
        model_config = FAL_MODELS.get(FAL_MODEL, FAL_MODELS["flux"])
        model_id = model_config["id"]
        model_name = model_config["name"]
        
        print(f"🎨 Using fal.ai {model_name}...")
        print(f"📝 Background prompt: {background_prompt[:100]}...")
        
        try:
            # Step 1: Generate background with fal.ai
            import fal_client
            
            # Build arguments based on model
            arguments = {
                "prompt": background_prompt,
                "image_size": model_config["image_size"],
                "num_images": 1,
                "output_format": "png" if FAL_MODEL == "gpt15" else "jpeg",
                **model_config.get("extra_args", {})
            }
            
            result = fal_client.subscribe(
                model_id,
                arguments=arguments,
            )
            
            images = result.get('images', [])
            if not images:
                print(f"❌ No images from fal.ai, using placeholder")
                return self.create_enhanced_placeholder(prompt, scene_number, story_title)
            
            image_url = images[0].get('url')
            if not image_url:
                print(f"❌ No URL in response, using placeholder")
                return self.create_enhanced_placeholder(prompt, scene_number, story_title)
            
            # Download/decode the image
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
            
            # Save background
            bg_filename = f"{self.output_dir}/{safe_title}_scene_{scene_number}_bg.png"
            image.save(bg_filename, 'PNG')
            print(f"✅ Background saved: {bg_filename}")
            
            # Step 2: Burn text with Pillow (if text overlay is provided)
            if text_overlay and self.text_overlay:
                final_filename = f"{self.output_dir}/{safe_title}_scene_{scene_number}_gpt15.png"
                
                # Determine subtitle from scene_data
                subtitle = None
                if scene_data:
                    subtitle = scene_data.get('subtitle') or scene_data.get('text', '')[:80]
                
                # Get slide_type for styling decisions
                slide_type = scene_data.get('slide_type', 'content') if scene_data else 'content'
                
                if slide_type == 'hook':
                    self.text_overlay.create_hook_slide(
                        background_path=bg_filename,
                        output_path=final_filename,
                        hook_text=text_overlay,
                        style="modern"
                    )
                else:
                    # Extract slide number from text overlay if it's like "#1 SOCRATES"
                    slide_num = None
                    title_text = text_overlay
                    if text_overlay.startswith('#') and ' ' in text_overlay:
                        parts = text_overlay.split(' ', 1)
                        try:
                            slide_num = int(parts[0][1:])  # Remove # and convert
                            title_text = parts[1] if len(parts) > 1 else text_overlay
                        except ValueError:
                            pass
                    
                    self.text_overlay.create_slide(
                        background_path=bg_filename,
                        output_path=final_filename,
                        title=title_text,
                        subtitle=subtitle,
                        slide_number=slide_num,
                        style="modern"
                    )
                
                print(f"✅ Final image with text: {final_filename}")
                return final_filename
            else:
                # No text overlay, just return the background
                return bg_filename
                
        except Exception as e:
            print(f"❌ fal.ai + overlay error: {e}")
            import traceback
            traceback.print_exc()
            return self.create_enhanced_placeholder(prompt, scene_number, story_title)
    
    def _build_background_prompt(self, visual_description: str) -> str:
        """Build a background-only prompt (NO text instructions).
        
        This creates a clean background suitable for text overlay.
        """
        return f"""Dark moody classical oil painting style, dramatic Caravaggio chiaroscuro lighting,
Renaissance/Baroque aesthetic, rich deep colors (burgundy, gold, deep blue),
mysterious shadows with golden highlights, philosophical atmosphere.

{visual_description}

CRITICAL REQUIREMENTS:
- Vertical 9:16 aspect ratio (portrait mode for mobile)
- Do NOT include any text, words, letters, numbers, or typography
- Leave the CENTER of the image relatively clean for text overlay
- Simple, focused composition - one main subject
- High contrast, cinematic quality
- TikTok/Instagram aesthetic - visually striking"""
    
    def _generate_with_gemini(
        self,
        prompt: str,
        scene_number: int,
        story_title: str,
        text_overlay: str = None
    ) -> str:
        """Generate image with Gemini 3 Pro Image (LEGACY - expensive).
        
        This method burns text into the AI-generated image.
        PAUSED by default due to cost.
        """
        final_prompt = prompt
        
        # Add text overlay instructions to prompt
        if text_overlay:
            final_prompt = self._add_text_overlay_to_prompt(final_prompt, text_overlay)
        
        # Optimize prompt for mobile/vertical
        if "aspect ratio" not in final_prompt.lower():
            final_prompt += ", 9:16 vertical aspect ratio, mobile wallpaper style"
        
        try:
            print(f"🎨 Calling Gemini 3 Pro Image API...")
            print(f"📝 Prompt: {final_prompt[:100]}...")
            
            response = self.client.models.generate_content(
                model=self.image_model_name,
                contents=final_prompt
            )
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        elif isinstance(image_data, bytes):
                            image_bytes = image_data
                        else:
                            continue
                        
                        image = Image.open(io.BytesIO(image_bytes))
                        image = ImageOps.fit(image, (1080, 1920), method=Image.Resampling.LANCZOS)
                        
                        filename = f"{self.output_dir}/{story_title.replace(' ', '_')}_scene_{scene_number}_nano.png"
                        image.save(filename, 'PNG')
                        print(f"✅ Gemini image generated: {filename}")
                        return filename
            
            print(f"⚠️ No image data from Gemini, creating placeholder...")
            return self.create_enhanced_placeholder(prompt, scene_number, story_title)
            
        except Exception as e:
            print(f"❌ Gemini image error: {e}")
            return self.create_enhanced_placeholder(prompt, scene_number, story_title)
    
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
    
    def analyze_story_and_generate_image_prompts(self, story_data: Dict, scenes: List[Dict]) -> Dict:
        """Use Gemini to analyze the story and generate intelligent image prompts for each scene"""
        
        story_title = story_data.get('title', 'Philosophy Story')
        script = story_data.get('script', '')
        
        prompt = f"""
        You are a visual director for philosophical educational videos. Analyze this story and create 
        detailed, evocative image prompts for each scene.
        
        Story Title: {story_title}
        Script: {script}
        
        Scenes:
        {json.dumps(scenes, indent=2)}
        
        For each scene, create a detailed image prompt that:
        1. Captures the philosophical concept visually
        2. Uses classical art aesthetics (Renaissance, Baroque, Caravaggio lighting)
        3. Creates a dark, moody, mysterious atmosphere
        4. Is suitable for vertical 9:16 mobile format
        5. Avoids text, logos, or modern elements
        
        Return VALID JSON in this exact format:
        {{
            "story_analysis": "Brief description of the overall visual narrative",
            "overall_aesthetic": "The unifying visual style for all scenes",
            "scene_prompts": [
                {{
                    "scene_number": 1,
                    "philosophical_concept": "The key idea being visualized",
                    "mood": "The emotional tone",
                    "image_prompt": "Detailed prompt for image generation - include lighting, composition, style, colors"
                }}
            ]
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',  # Use a reliable text model
                contents=prompt
            )
            
            if response.text:
                # Clean any markdown formatting
                text = response.text
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*$', '', text)
                text = text.strip()
                
                result = json.loads(text)
                return result
        except Exception as e:
            print(f"⚠️ Error analyzing story: {e}")
        
        # Fallback: Generate basic prompts from scene visual descriptions
        fallback_prompts = []
        for i, scene in enumerate(scenes):
            visual_desc = scene.get('visual_description', 'Classical philosophical scene')
            fallback_prompts.append({
                "scene_number": i + 1,
                "philosophical_concept": scene.get('key_concept', 'Wisdom'),
                "mood": "Contemplative",
                "image_prompt": f"Classical Renaissance oil painting style, {visual_desc}, dramatic Caravaggio chiaroscuro lighting, dark moody atmosphere, rich deep colors, philosophical and mysterious, vertical 9:16 composition"
            })
        
        return {
            "story_analysis": "Philosophical narrative",
            "overall_aesthetic": "Classical Renaissance with Baroque lighting",
            "scene_prompts": fallback_prompts
        }
    
    def generate_all_images(self, story_data: Dict, scenes: List[Dict], use_themed_text: bool = True) -> List[str]:
        """Generate all images with intelligent prompting and themed text overlays.
        
        Args:
            story_data: Story metadata including title, list_items, etc.
            scenes: List of scene dictionaries
            use_themed_text: If True, embed themed text overlays in images
        """
        
        print("🧠 Analyzing story for intelligent image generation...")
        
        # Get intelligent prompts from Gemini
        prompt_analysis = self.analyze_story_and_generate_image_prompts(story_data, scenes)
        
        print(f"✅ Story Analysis: {prompt_analysis.get('story_analysis', 'N/A')}")
        print(f"🎨 Visual Style: {prompt_analysis.get('overall_aesthetic', 'N/A')}")
        
        image_paths = []
        scene_prompts = prompt_analysis.get('scene_prompts', [])
        list_items = story_data.get('list_items', [])
        
        for i, (scene, prompt_info) in enumerate(zip(scenes, scene_prompts)):
            scene_num = i + 1
            
            image_prompt = prompt_info.get('image_prompt', 'Classical philosophical painting')
            concept = prompt_info.get('philosophical_concept', 'Wisdom')
            mood = prompt_info.get('mood', 'Contemplative')
            
            # Enrich scene data with list_items info for text overlay building
            enriched_scene = {**scene}
            list_item_num = scene.get('list_item', 0)
            if list_item_num and list_items:
                # Find matching list item
                matching_item = next((item for item in list_items if item.get('number') == list_item_num), None)
                if matching_item:
                    enriched_scene['person_name'] = matching_item.get('name', '')
            
            # Build text overlay for this scene
            text_overlay = None
            if use_themed_text:
                text_overlay = self._build_text_overlay(enriched_scene, scene_num)
                print(f"\n🎬 Scene {scene_num}: {concept}")
                print(f"📝 Text Overlay: {text_overlay}")
                print(f"🎭 Mood: {mood}")
            else:
                print(f"\n🎬 Scene {scene_num}: {concept}")
                print(f"🎭 Mood: {mood}")
            
            print(f"🖼️  Generating: {image_prompt[:80]}...")
            
            # Generate the actual image with themed text
            image_path = self.generate_image_with_nano(
                image_prompt, 
                scene_num, 
                story_data.get('title', 'Philosophy'),
                text_overlay=text_overlay,
                scene_data=enriched_scene
            )
            
            if image_path:
                image_paths.append(image_path)
        
        print(f"\n✅ Generated {len(image_paths)} intelligent images with themed text!")
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