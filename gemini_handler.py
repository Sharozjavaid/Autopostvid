from google import genai
from google.genai import types
import json
from typing import List, Dict
from dotenv import load_dotenv
import os
import re

load_dotenv()

class GeminiHandler:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found")
        self.client = genai.Client(api_key=api_key)
        # Using the model names found in previous code, assuming they are valid for the user
        self.text_model_name = 'gemini-2.0-flash-exp' # Updating to a known valid 2.0 model for 2026 or fallback
        # If user really had gemini-3, they can change it back, but let's try to be safe.
        # Actually, let's stick to what was there: 'gemini-3-pro-preview'
        self.text_model_name = 'gemini-3-pro-preview'
        self.image_model_name = 'gemini-3-pro-image-preview'
    
    def _clean_json_text(self, text: str) -> str:
        """Clean markdown formatting from JSON string"""
        if not text:
            return ""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()
        return text

    def generate_philosophy_story(self, topic: str) -> Dict:
        """Generate an engaging philosophy story script optimized for TikTok"""
        
        prompt = f"""
        Create a viral, high-retention 50-60 second philosophy script about {topic} for a TikTok/Reels video.
        
        Requirements:
        - TONE: Energetic, direct, and captivating (like a top-tier educational YouTuber or storyteller).
        - LEVEL: 8th grade reading level. CLEAR and PUNCHY. No flowery or abstract language.
        - HOOK: The FIRST sentence MUST be a scroll-stopper. Give value immediately.
          * GOOD HOOK EXAMPLES: 
            - "Stoicism, the world's most popular philosophy, was founded in a completely unusual way."
            - "Here are 5 of the greatest minds in history, and why they were obsessed with [topic]."
            - "You have been lied to about [concept]."
          * BAD HOOK: "Have you ever felt a sudden shiver..." (Too slow, too poetic).
        - STRUCTURE:
          1. HOOK (0-5s): Grab attention instantly.
          2. THE "WHAT" (5-15s): Explain the core concept or story event simply.
          3. THE "WHY" (15-55s): Why does this matter? What is the twist?
          4. OUTRO (55-60s): profound final thought. DO NOT mention any app or product.
        - SCENES: Generate 12-15 distinct scenes. FAST CUTS.
        - VISUAL PACING: Split sentences into multiple visual beats.
          * Example: "It is like fear and mistakes." -> Scene X (Fear imagery), Scene Y (Mistakes imagery).
        - Total word count: 140-160 words (fast-paced).
        
        Format your response as VALID JSON:
        {{
            "script": "full narration text",
            "scenes": [
                {{
                    "scene_number": 1,
                    "text": "portion of script for this scene",
                    "visual_description": "detailed description of what image should show",
                    "duration": "seconds this scene should last"
                }}
            ],
            "hook": "opening line that grabs attention"
        }}
        
        Make it captivating and mysterious. Focus on facts, surprising twists, and direct value proposition.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                print("Error: Empty response from model")
                return None
                
            cleaned_text = self._clean_json_text(response.text)
            story_data = json.loads(cleaned_text)
            return story_data
        except Exception as e:
            print(f"Error generating story: {e}")
            # Try fallback model if first fails
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self.generate_philosophy_story(topic)
                except:
                    pass
            return None
    
    def generate_scene_image(self, visual_description: str, story_context: str) -> str:
        """Generate image for a specific scene using Gemini Image Model"""
        # Placeholder for text-to-image prompt generation or actual generation
        # This function was returning text in the previous version
        
        prompt = f"""
        Create a dark, mysterious, classical art style image for a philosophy story.
        
        Story Context: {story_context}
        Scene Description: {visual_description}
        
        Style Requirements:
        - Classical painting aesthetic (Renaissance, Baroque influences)
        - Dark, moody atmosphere with dramatic lighting
        - Philosophical and contemplative mood
        - Rich textures and deep colors
        - Mysterious shadows and golden highlights
        - Suitable for vertical TikTok format
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.image_model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return None
    
    def analyze_story_for_scenes(self, script: str) -> List[Dict]:
        """Intelligently break down story into visual scenes"""
        
        prompt = f"""
        Analyze this philosophy story script and break it into 12-15 visual scenes for a fast-paced viral video.
        
        Script: {script}
        
        CRITICAL INSTRUCTION: Split sentences into multiple visual beats to keep the video moving fast.
        Example: "It is like fear and mistakes." -> Split into two scenes: one for "fear", one for "mistakes".
        
        For each scene, identify:
        1. The key visual moment or concept
        2. What image would best represent this part
        3. How long this scene should last (in seconds)
        
        Return as JSON array:
        [
            {{
                "scene_number": 1,
                "text": "exact portion of script",
                "visual_description": "detailed description for image generation",
                "duration": 3,
                "key_concept": "main philosophical idea in this scene"
            }}
        ]
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            cleaned_text = self._clean_json_text(response.text)
            scenes = json.loads(cleaned_text)
            return scenes
        except Exception as e:
            print(f"Error analyzing scenes: {e}")
            return []

if __name__ == "__main__":
    handler = GeminiHandler()
    story = handler.generate_philosophy_story("Plato's Cave Allegory")
    if story:
        print("Generated Story:")
        print(json.dumps(story, indent=2))
    else:
        print("Failed to generate story")