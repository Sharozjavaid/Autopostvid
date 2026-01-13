#!/usr/bin/env python3
"""
TikTok Caption Generator using OpenAI GPT-5 nano
Generates engaging captions with relevant hashtags for philosophy videos
"""

import os
from dotenv import load_dotenv

load_dotenv()


class CaptionGenerator:
    def __init__(self):
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-5-nano"  # Super cheap model for caption generation
            print(f"✅ Caption Generator initialized with model: {self.model}")
            
        except ImportError:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Error initializing OpenAI client: {e}")
    
    def generate_caption(self, topic: str, title: str = None) -> str:
        """
        Generate a TikTok caption with hashtags for a philosophy video.
        
        Args:
            topic: The philosophy topic of the video
            title: Optional video title for more context
        
        Returns:
            A TikTok-ready caption with hashtags
        """
        
        context = title if title else topic
        
        prompt = f"""Generate a short, engaging TikTok caption for a philosophy video about: {context}

Requirements:
- Keep it under 150 characters (excluding hashtags)
- Make it thought-provoking and scroll-stopping
- Use a conversational, engaging tone
- Add 5-7 relevant hashtags at the end
- MUST include #PhilosophizeMeApp as the FIRST hashtag
- Other hashtags should be relevant to philosophy, the specific topic, and TikTok trends
- Include #stoicism #philosophy #wisdom and other relevant tags

Example format:
"This changed how I see everything... 🤯 #PhilosophizeMeApp #stoicism #philosophy #wisdom #mindset #fyp"

Generate only the caption text, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a social media expert who creates viral TikTok captions for philosophy content."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            caption = response.choices[0].message.content.strip()
            
            # Ensure #PhilosophizeMeApp is included (safety check)
            if "#PhilosophizeMeApp" not in caption:
                caption += " #PhilosophizeMeApp"
            
            print(f"✅ Caption generated: {caption[:50]}...")
            return caption
            
        except Exception as e:
            print(f"❌ Caption generation error: {e}")
            # Return a fallback caption if generation fails
            return f"Deep thoughts on {topic} 🧠 #PhilosophizeMeApp #philosophy #wisdom #fyp #mindset"


if __name__ == "__main__":
    # Test the caption generator
    generator = CaptionGenerator()
    
    test_topics = [
        "Stoicism and Marcus Aurelius",
        "Plato's Cave Allegory",
        "Nietzsche's Will to Power"
    ]
    
    for topic in test_topics:
        print(f"\n📝 Topic: {topic}")
        caption = generator.generate_caption(topic)
        print(f"📱 Caption: {caption}")
        print("-" * 50)
