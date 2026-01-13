#!/usr/bin/env python3
"""
Unified Content Generator

Consolidates script generation (list, narrative, slideshow) into ONE intelligent prompt.
The model chooses the best approach based on the topic.

This replaces the separate prompts in gemini_handler.py with a single, versatile prompt.
"""

from google import genai
from google.genai import types
import json
import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class UnifiedContentGenerator:
    """
    Single intelligent prompt that handles:
    - List-style content ("5 philosophers who...")
    - Narrative stories ("Plato's Cave Allegory")
    - Slideshow content (static TikTok slides)
    
    The model decides the best approach based on the topic.
    """
    
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.0-flash-exp'  # Use flash for speed/cost
        
        print(f"✅ UnifiedContentGenerator initialized (model: {self.model_name})")
    
    def _clean_json(self, text: str) -> str:
        """Clean markdown formatting from JSON response"""
        if not text:
            return ""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        return text.strip()
    
    def generate_content(
        self,
        topic: str,
        num_slides: int = 6,
        target_duration: int = 60,
        output_format: str = "slideshow"  # "slideshow", "video_script", "auto"
    ) -> Optional[Dict]:
        """
        Generate content for any topic using a unified intelligent prompt.
        
        Args:
            topic: The content topic (e.g., "5 philosophers who changed the world")
            num_slides: Number of slides/scenes to generate (default 6)
            target_duration: Target duration in seconds (for video scripts)
            output_format: 
                - "slideshow": Static TikTok slides with display_text + subtitle
                - "video_script": Full narration with scene-by-scene text
                - "auto": Let the model decide based on topic
        
        Returns:
            Structured content data with slides, script, etc.
        """
        
        prompt = self._build_unified_prompt(topic, num_slides, target_duration, output_format)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                print("❌ Empty response from model")
                return None
            
            cleaned = self._clean_json(response.text)
            content_data = json.loads(cleaned)
            
            # Add metadata
            content_data['topic'] = topic
            content_data['generated_with'] = 'unified_content_generator'
            
            print(f"✅ Generated: {content_data.get('title', 'Untitled')}")
            print(f"   Type: {content_data.get('content_type', 'unknown')}")
            print(f"   Slides: {len(content_data.get('slides', []))}")
            
            return content_data
            
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_unified_prompt(
        self,
        topic: str,
        num_slides: int,
        target_duration: int,
        output_format: str
    ) -> str:
        """Build the unified prompt that handles all content types."""
        
        return f"""
You are an EXPERT VIRAL CONTENT CREATOR for TikTok/Instagram philosophy content.

Your job is to create scroll-stopping content that makes people THINK and ENGAGE.

TOPIC: {topic}

OUTPUT FORMAT: {output_format}
NUMBER OF SLIDES: {num_slides}
{"TARGET DURATION: " + str(target_duration) + " seconds" if output_format == "video_script" else ""}

═══════════════════════════════════════════════════════════════════
STEP 1: ANALYZE THE TOPIC
═══════════════════════════════════════════════════════════════════

First, determine the CONTENT TYPE based on the topic:

**LIST** - Use when topic mentions specific numbers or multiple items:
- "5 philosophers who..."
- "Top 10 quotes from..."
- "3 lessons from..."
Pattern: Rankings, collections, numbered items

**NARRATIVE** - Use when topic is a story or single concept:
- "Plato's Cave Allegory"
- "The founding of Stoicism"
- "Marcus Aurelius and the slave"
Pattern: Stories, allegories, historical moments

**LESSONS/ARGUMENT** - Use when topic makes a claim or teaches:
- "Why philosophy beats therapy"
- "How Stoicism cures anxiety"
- "What billionaires learned from philosophers"
Pattern: Arguments, teachings, transformations

═══════════════════════════════════════════════════════════════════
STEP 2: CRAFT THE HOOK (MOST IMPORTANT!)
═══════════════════════════════════════════════════════════════════

The FIRST SLIDE is EVERYTHING. It must:
1. Make them STOP scrolling
2. Create CURIOSITY ("Wait, what?")
3. Connect to PHILOSOPHY (even indirectly)

**HOOK TRANSFORMATION FORMULAS:**

❌ BORING: "5 famous philosophers"
✅ VIRAL: "5 MINDS THAT CHANGED HOW HUMANS THINK FOREVER"

❌ BORING: "Stoic quotes for life"
✅ VIRAL: "A ROMAN EMPEROR'S DIARY THAT BILLIONAIRES READ EVERY MORNING"

❌ BORING: "Plato's cave allegory explained"
✅ VIRAL: "YOU'RE PROBABLY LIVING IN A CAVE RIGHT NOW"

**HOOK PATTERNS THAT WORK:**
- [MODERN SUCCESS] + [ANCIENT WISDOM]: "THE 2000-YEAR-OLD SECRET STEVE JOBS FOLLOWED"
- [PROVOCATIVE CLAIM]: "THE ONE QUESTION SCIENCE WILL NEVER ANSWER"
- [MYSTERY]: "THEY KNEW THE ANSWER BEFORE WE ASKED THE QUESTION"
- [DRAMATIC CONTRAST]: "HE RULED AN EMPIRE BUT ASKED ONE QUESTION EVERY NIGHT"

═══════════════════════════════════════════════════════════════════
STEP 3: STRUCTURE BY CONTENT TYPE
═══════════════════════════════════════════════════════════════════

**FOR LIST CONTENT:**
- Slide 0: HOOK - "5 MINDS THAT MASTERED INNER PEACE"
- Slides 1-N: Each person/concept with DRAMATIC subtitle
- Final Slide: Challenge or call to action

Each list item needs:
- display_text: "MARCUS AURELIUS" (2-4 words, ALL CAPS)
- subtitle: "He ruled Rome. Every night he asked: 'Was I good today?'" (8-15 words)

**FOR NARRATIVE CONTENT:**
- Slide 0: HOOK - Start with ACTION or TENSION
- Slides 1-2: Build the scene (who, where, stakes)
- Slides 3-4: The KEY MOMENT (don't rush!)
- Slides 5+: Meaning and lesson

**FOR LESSONS/ARGUMENT:**
- Slide 0: HOOK - Bold claim or question
- Slides 1-N: Each reason/lesson with evidence
- Final Slide: Summary or call to action

═══════════════════════════════════════════════════════════════════
STEP 4: VISUAL DESCRIPTIONS (CRITICAL!)
═══════════════════════════════════════════════════════════════════

Each slide needs a visual_description that MATCHES the slide subject:

**MATCH THE SUBJECT:**
- Slide about Steve Jobs → "Steve Jobs silhouette in black turtleneck, minimalist background"
- Slide about Marcus Aurelius → "Roman emperor in purple robes writing by candlelight"
- Slide about a lesson → Visual metaphor for that lesson

**LEAVE SPACE FOR TEXT:**
- The center of the image should be clean for text overlay
- Suggest "silhouette" or "figure in shadows" to avoid face conflicts with text
- Dark backgrounds work best (text pops)

**NO TEXT IN VISUAL DESCRIPTION:**
- The visual_description is for the BACKGROUND IMAGE only
- Text will be added separately

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════

Return VALID JSON in this EXACT structure:

{{
    "title": "Short catchy title for the content",
    "content_type": "list" | "narrative" | "lessons",
    "hook": "The attention-grabbing first line",
    "total_slides": {num_slides},
    "slides": [
        {{
            "slide_number": 0,
            "slide_type": "hook",
            "display_text": "BOLD HOOK TEXT HERE",
            "subtitle": "",
            "visual_description": "Epic, dramatic background image description without text",
            "person_name": null,
            "key_concept": "What this slide is about"
        }},
        {{
            "slide_number": 1,
            "slide_type": "person" | "lesson" | "moment" | "quote",
            "display_text": "MAIN TEXT",
            "subtitle": "Secondary explanatory text (8-15 words, punchy)",
            "visual_description": "Background image description matching the subject",
            "person_name": "Name if applicable",
            "key_concept": "Main idea"
        }},
        // ... more slides ...
        {{
            "slide_number": {num_slides - 1},
            "slide_type": "outro",
            "display_text": "CLOSING TEXT",
            "subtitle": "Final thought or call to action",
            "visual_description": "Inspiring closing image",
            "person_name": null,
            "key_concept": "call_to_action"
        }}
    ],
    "list_items": [
        // Only for list content - summary of each item
        {{
            "number": 1,
            "name": "Person/Concept Name",
            "key_quote": "Their signature quote or idea",
            "why_matters": "One sentence on why this matters"
        }}
    ]
}}

**RULES:**
- display_text: 2-6 words, ALL CAPS, no periods
- subtitle: 8-15 words, punchy, emotional, ends with period or question
- visual_description: 15-30 words, specific, no text mentioned
- Always exactly {num_slides} slides

Now generate the content for: {topic}
"""


def test_unified_generator():
    """Test the unified content generator with different topic types"""
    
    generator = UnifiedContentGenerator()
    
    test_topics = [
        # List-style
        "5 philosophers who mastered inner peace",
        # Narrative
        "Marcus Aurelius and the slave who spilled oil",
        # Lessons/Argument
        "Why ancient philosophy beats modern therapy"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING UNIFIED CONTENT GENERATOR")
    print("=" * 60)
    
    for topic in test_topics:
        print(f"\n📝 Topic: {topic}")
        print("-" * 40)
        
        result = generator.generate_content(topic, num_slides=6)
        
        if result:
            print(f"✅ Title: {result.get('title')}")
            print(f"   Type: {result.get('content_type')}")
            print(f"   Hook: {result.get('hook', '')[:50]}...")
            print(f"   Slides: {len(result.get('slides', []))}")
            
            # Show first slide
            slides = result.get('slides', [])
            if slides:
                first = slides[0]
                print(f"\n   First Slide:")
                print(f"   - display_text: {first.get('display_text')}")
                print(f"   - subtitle: {first.get('subtitle', '')[:50]}")
                print(f"   - visual: {first.get('visual_description', '')[:50]}...")
        else:
            print("❌ Failed to generate content")
        
        print()


if __name__ == "__main__":
    test_unified_generator()
