#!/usr/bin/env python3
"""
Unified Image Generator - Seamlessly switch between Nano (Gemini) and OpenAI models
For use in both Streamlit app and automation pipeline
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class ImageModel(Enum):
    """Available image generation models"""
    NANO = "nano"  # Gemini 3 Pro Image
    OPENAI_DALLE3 = "openai-dalle3"
    OPENAI_GPT_IMAGE = "openai-gpt-image-1.5"


# Default model for automation
DEFAULT_MODEL = ImageModel.NANO


class UnifiedImageGenerator:
    """
    Unified interface for image generation across different providers.
    
    Usage:
        # Use default model (Nano)
        gen = UnifiedImageGenerator()
        
        # Use specific model
        gen = UnifiedImageGenerator(model=ImageModel.OPENAI_DALLE3)
        
        # Switch model at runtime
        gen.set_model(ImageModel.OPENAI_GPT_IMAGE)
        
        # Generate images
        paths = gen.generate_scene_image(scene_data, story_title)
    """
    
    def __init__(self, model: ImageModel = None):
        self.model = model or DEFAULT_MODEL
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Lazy-loaded generators
        self._nano_generator = None
        self._openai_generator = None
        
        print(f"🎨 UnifiedImageGenerator initialized with model: {self.model.value}")
    
    def set_model(self, model: ImageModel):
        """Switch to a different model"""
        self.model = model
        print(f"🔄 Switched to model: {self.model.value}")
    
    @property
    def nano_generator(self):
        """Lazy-load Nano (Gemini) generator"""
        if self._nano_generator is None:
            from smart_image_generator import SmartImageGenerator
            self._nano_generator = SmartImageGenerator()
        return self._nano_generator
    
    @property
    def openai_generator(self):
        """Lazy-load OpenAI generator"""
        if self._openai_generator is None:
            from openai_image_generator import OpenAIImageGenerator
            model_slug = "dall-e-3" if self.model == ImageModel.OPENAI_DALLE3 else "gpt-image-1.5"
            self._openai_generator = OpenAIImageGenerator(model=model_slug)
        return self._openai_generator
    
    def _reinit_openai_if_needed(self):
        """Reinitialize OpenAI generator if model changed"""
        if self._openai_generator is not None:
            expected_model = "dall-e-3" if self.model == ImageModel.OPENAI_DALLE3 else "gpt-image-1.5"
            if self._openai_generator.model != expected_model:
                from openai_image_generator import OpenAIImageGenerator
                self._openai_generator = OpenAIImageGenerator(model=expected_model)
    
    def generate_scene_image(
        self, 
        scene_data: Dict, 
        story_title: str,
        prompt_override: str = None
    ) -> Optional[str]:
        """
        Generate image for a single scene.
        
        Args:
            scene_data: Scene dictionary with visual_description, text, key_concept, scene_number
            story_title: Title of the story (for filename)
            prompt_override: Optional custom prompt (overrides auto-generated prompt)
        
        Returns:
            Path to generated image, or None if failed
        """
        scene_num = scene_data.get('scene_number', 1)
        
        if self.model == ImageModel.NANO:
            # Use Nano (Gemini)
            if prompt_override:
                path = self.nano_generator.generate_image_with_nano(
                    prompt=prompt_override,
                    scene_number=scene_num,
                    story_title=story_title,
                    prompt_override=prompt_override
                )
            else:
                # Let Nano construct its own prompt from scene data
                visual_desc = scene_data.get('visual_description', '')
                key_concept = scene_data.get('key_concept', '')
                default_prompt = f"Classical Old Master painting style, Caravaggio and Rembrandt influences, dramatic chiaroscuro lighting, {visual_desc}, {key_concept}"
                path = self.nano_generator.generate_image_with_nano(
                    prompt=default_prompt,
                    scene_number=scene_num,
                    story_title=story_title
                )
            return path
        
        else:
            # Use OpenAI
            self._reinit_openai_if_needed()
            
            if prompt_override:
                paths = self.openai_generator.generate_image(
                    prompt=prompt_override,
                    scene_number=scene_num,
                    story_title=story_title
                )
            else:
                paths = self.openai_generator.generate_philosophy_image(
                    scene_data=scene_data,
                    story_title=story_title
                )
            
            return paths[0] if paths else None
    
    def generate_all_images(
        self, 
        story_data: Dict, 
        scenes: List[Dict],
        global_style: str = None
    ) -> List[str]:
        """
        Generate images for all scenes in a story.
        
        Args:
            story_data: Full story dictionary with title, script, etc.
            scenes: List of scene dictionaries
            global_style: Optional global style prompt to apply to all scenes
        
        Returns:
            List of paths to generated images
        """
        story_title = story_data.get('title', 'Philosophy')
        image_paths = []
        
        print(f"🎨 Generating {len(scenes)} images with {self.model.value}...")
        
        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            print(f"  Scene {scene_num}/{len(scenes)}...")
            
            # Construct prompt if global style provided
            if global_style:
                visual_desc = scene.get('visual_description', '')
                key_concept = scene.get('key_concept', '')
                prompt = f"{global_style}, {visual_desc}, {key_concept}"
            else:
                prompt = None
            
            path = self.generate_scene_image(
                scene_data=scene,
                story_title=story_title,
                prompt_override=prompt
            )
            
            if path:
                image_paths.append(path)
            else:
                print(f"  ⚠️ Failed to generate image for scene {scene_num}")
        
        print(f"✅ Generated {len(image_paths)}/{len(scenes)} images")
        return image_paths
    
    @staticmethod
    def get_available_models() -> List[ImageModel]:
        """Get list of available models based on configured API keys"""
        available = [ImageModel.NANO]  # Nano always available if Google API key exists
        
        if os.getenv('OPENAI_API_KEY'):
            available.append(ImageModel.OPENAI_DALLE3)
            available.append(ImageModel.OPENAI_GPT_IMAGE)
        
        return available
    
    @staticmethod
    def model_from_string(model_str: str) -> ImageModel:
        """Convert string to ImageModel enum"""
        mapping = {
            "nano": ImageModel.NANO,
            "gemini": ImageModel.NANO,
            "openai-dalle3": ImageModel.OPENAI_DALLE3,
            "dalle3": ImageModel.OPENAI_DALLE3,
            "dall-e-3": ImageModel.OPENAI_DALLE3,
            "openai-gpt-image-1.5": ImageModel.OPENAI_GPT_IMAGE,
            "gpt-image-1.5": ImageModel.OPENAI_GPT_IMAGE,
            "gpt-image": ImageModel.OPENAI_GPT_IMAGE,
        }
        return mapping.get(model_str.lower(), ImageModel.NANO)


# Convenience function for automation
def create_image_generator(model: str = "nano") -> UnifiedImageGenerator:
    """
    Factory function to create image generator with specified model.
    
    Args:
        model: Model name string ("nano", "openai-dalle3", "openai-gpt-image-1.5")
    
    Returns:
        Configured UnifiedImageGenerator instance
    """
    model_enum = UnifiedImageGenerator.model_from_string(model)
    return UnifiedImageGenerator(model=model_enum)


# Test
if __name__ == "__main__":
    print("🧪 Testing UnifiedImageGenerator")
    print("=" * 50)
    
    # Show available models
    available = UnifiedImageGenerator.get_available_models()
    print(f"Available models: {[m.value for m in available]}")
    
    # Test with Nano
    gen = create_image_generator("nano")
    
    test_scene = {
        'scene_number': 1,
        'text': 'You sit in darkness, believing shadows are reality.',
        'visual_description': 'Dark cave with chained figures watching shadows',
        'key_concept': 'Illusion of Reality'
    }
    
    print(f"\nTest scene: {test_scene['key_concept']}")
    print(f"Model: {gen.model.value}")
    
    # Uncomment to actually generate:
    # path = gen.generate_scene_image(test_scene, "Test_Story")
    # print(f"Generated: {path}")
