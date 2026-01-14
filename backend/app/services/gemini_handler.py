from google import genai
from google.genai import types
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
import re

from .prompt_config import (
    get_script_prompt,
    get_content_type_config,
    CONTENT_TYPES,
)

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

    def _detect_content_type(self, topic: str) -> str:
        """
        Detect if the topic is a list-style slideshow or a narrative story.
        
        Returns:
            'list' - for topics like "5 philosophers who...", "Top 10 quotes..."
            'story' - for narrative topics like "Plato's Cave Allegory"
        """
        topic_lower = topic.lower()
        
        # Patterns that indicate list-style content
        list_patterns = [
            r'^\d+\s+',                          # Starts with number: "5 philosophers..."
            r'^top\s+\d+',                       # "Top 5..."
            r'^best\s+\d+',                      # "Best 10..."
            r'^\d+\s*(of\s+the\s+)?(best|greatest|most|top|powerful|influential)',  # "5 of the most..."
            r'(quotes?|sayings?|lessons?|rules?|principles?|secrets?|tips?|facts?|ideas?|concepts?)\s*(from|by|of)',  # "quotes from philosophers"
            r'(philosophers?|thinkers?|stoics?|minds?)\s*(who|that|with)',  # "philosophers who changed..."
            r'^(here are|these are)\s+\d+',      # "Here are 5..."
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, topic_lower):
                return 'list'
        
        # Additional keyword combinations that suggest list content
        list_keywords = ['philosophers', 'thinkers', 'quotes', 'lessons', 'principles', 
                         'secrets', 'rules', 'facts', 'schools', 'founders', 'ideas']
        number_words = ['five', 'ten', 'three', 'four', 'six', 'seven', 'eight', 'nine']
        
        has_number = bool(re.search(r'\d+', topic_lower)) or any(nw in topic_lower for nw in number_words)
        has_list_keyword = any(kw in topic_lower for kw in list_keywords)
        
        if has_number and has_list_keyword:
            return 'list'
        
        return 'story'

    def _generate_list_content(self, topic: str, num_scenes: int = 10, words_per_scene: int = 15) -> Dict:
        """Generate list-style slideshow content (e.g., '5 philosophers with great quotes')
        
        Args:
            topic: The content topic
            num_scenes: Target number of scenes (default 10)
            words_per_scene: Target words per scene for audio sync (default 15 = ~6 seconds)
        """
        
        total_words = num_scenes * words_per_scene
        
        prompt = f"""
        You are a LEGENDARY STORYTELLER creating a list-style video that will go VIRAL.
        Think: the energy of a sports announcer + the wisdom of a philosophy professor + the accessibility of a 5th grade teacher.
        
        Your topic: {topic}
        
        🎭 YOUR STORYTELLING PERSONA:
        - You make philosophy EXCITING and ACCESSIBLE
        - You speak to a 5th grader but respect their intelligence
        - Every word is chosen for MAXIMUM IMPACT
        - You don't just list facts — you make people FEEL why each item matters
        
        🔥 THE KEY TO GREAT LIST VIDEOS:
        Each list item should feel like a MINI-STORY, not just a dry fact.
        
        ❌ BAD (boring): "Socrates was a Greek philosopher who asked questions."
        ✅ GOOD (captivating): "Socrates asked so many questions, they literally KILLED him for it. His crime? Making people think."
        
        ❌ BAD (forgettable): "Marcus Aurelius wrote about controlling emotions."
        ✅ GOOD (memorable): "He ruled the entire Roman Empire, yet wrote in his journal: 'You could be dead tomorrow. What are you so angry about?'"
        
        📖 FOR EACH LIST ITEM, INCLUDE:
        1. A DRAMATIC HOOK about the person/concept (what makes them special?)
        2. The CORE IDEA or QUOTE (the thing people will remember)
        3. WHY IT MATTERS (connect it to the viewer's life)
        
        Use vivid language:
        - "This man was so wise that..."
        - "His words are still quoted 2000 years later..."
        - "What he said next shocked everyone..."
        - "This single idea changed the entire Western world..."
        
        ⚠️ TIMING CONSTRAINT (MUST FOLLOW):
        - Each scene MUST have EXACTLY 12-15 words (creates 5-6 seconds of speech)
        - Total: {num_scenes} scenes × {words_per_scene} words = ~{total_words} words
        - COUNT YOUR WORDS. If a scene has <12 or >15 words, REWRITE IT.
        
        📝 STRUCTURE FOR LIST VIDEOS:
        1. HOOK (scene 1): Promise something POWERFUL. Be specific.
           * GOOD: "These five ancient minds said things so powerful, people still live by them today."
           * BAD: "Have you ever wondered about philosophy?"
        2. THE LIST (scenes 2-8/9): Each item gets 1-2 scenes
           - Scene A: Dramatic introduction (who they are, why they matter)
           - Scene B: The key quote/idea/contribution
        3. OUTRO (final scene): Challenge them or leave them thinking.
        
        Generate exactly {num_scenes} scenes.
        
        Format as VALID JSON:
        {{
            "script": "full narration text - the complete voiceover script",
            "scenes": [
                {{
                    "scene_number": 1,
                    "text": "portion of script for this scene - EXACTLY 12-15 WORDS",
                    "word_count": 14,
                    "target_duration": 6,
                    "visual_description": "vivid, specific image description",
                    "slide_subject": "BOLD TEXT OVERLAY - e.g., '#1 SOCRATES' or 'THE TRUTH'",
                    "list_item": 0,
                    "key_concept": "main idea for this scene"
                }}
            ],
            "hook": "the attention-grabbing opening line",
            "list_items": [
                {{
                    "number": 1,
                    "name": "Name of philosopher/concept",
                    "quote_or_idea": "The main quote or key idea",
                    "explanation": "Why this matters - make it personal and impactful"
                }}
            ],
            "total_word_count": {total_words},
            "estimated_duration_seconds": {num_scenes * 6}
        }}
        
        SLIDE_SUBJECT EXAMPLES:
        - Hook: "5 MINDS THAT CHANGED EVERYTHING", "LEGENDS OF WISDOM"
        - List items: "#1 SOCRATES", "#2 MARCUS AURELIUS"
        - Key concepts: "QUESTION EVERYTHING", "MEMENTO MORI"
        - Outro: "YOUR TURN", "CHOOSE WISELY"
        
        Remember: You're not reading Wikipedia. You're making someone stop scrolling because they NEED to hear what comes next.
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
            story_data['content_type'] = 'list'
            return story_data
        except Exception as e:
            print(f"Error generating list content: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self._generate_list_content(topic)
                except:
                    pass
            return None

    def generate_philosophy_story(self, topic: str, num_scenes: int = 10, words_per_scene: int = 15) -> Dict:
        """Generate an engaging philosophy script optimized for TikTok.
        
        Automatically detects if the topic is:
        - A LIST (e.g., "5 philosophers who...", "Top quotes from...")
        - A STORY (e.g., "Plato's Cave Allegory", "The founding of Stoicism")
        
        Uses specialized prompts for each type.
        
        Args:
            topic: The content topic
            num_scenes: Target number of scenes (default 10, produces ~60s video)
            words_per_scene: Target words per scene (default 15, ~6s of speech each)
        """
        # Detect content type and route to appropriate generator
        content_type = self._detect_content_type(topic)
        print(f"Detected content type for '{topic}': {content_type}")
        print(f"Generating {num_scenes} scenes × {words_per_scene} words = ~{num_scenes * 6}s video")
        
        if content_type == 'list':
            return self._generate_list_content(topic, num_scenes, words_per_scene)
        
        # Default: narrative story
        return self._generate_narrative_story(topic, num_scenes, words_per_scene)
    
    def generate_timed_script(
        self, 
        topic: str, 
        target_duration: int = 60,
        clip_duration: int = 6
    ) -> Dict:
        """Generate a script optimized for audio-video synchronization.
        
        This is the primary method for the automated pipeline. It calculates
        the optimal number of scenes and word counts to hit the target duration.
        
        Args:
            topic: The content topic
            target_duration: Target video duration in seconds (default 60)
            clip_duration: Duration per video clip in seconds (5 or 6)
            
        Returns:
            Script data with timing-aware scene structure
        """
        # Calculate optimal scene count
        num_scenes = target_duration // clip_duration
        
        # Words per scene based on speech rate (~2.5 words/second)
        words_per_scene = int(clip_duration * 2.5)  # 12-13 for 5s, 15 for 6s
        
        print(f"🎬 Generating timed script:")
        print(f"   Target duration: {target_duration}s")
        print(f"   Clip duration: {clip_duration}s")
        print(f"   Scenes: {num_scenes}")
        print(f"   Words per scene: {words_per_scene}")
        
        # Generate the script with these constraints
        story_data = self.generate_philosophy_story(topic, num_scenes, words_per_scene)
        
        if story_data:
            # Add timing metadata
            story_data['timing_config'] = {
                'target_duration': target_duration,
                'clip_duration': clip_duration,
                'num_scenes': num_scenes,
                'words_per_scene': words_per_scene,
                'expected_total_words': num_scenes * words_per_scene
            }
            
            # Validate word counts
            actual_words = sum(len(s.get('text', '').split()) for s in story_data.get('scenes', []))
            story_data['timing_config']['actual_total_words'] = actual_words
            
            variance = actual_words - (num_scenes * words_per_scene)
            story_data['timing_config']['word_variance'] = variance
            
            print(f"   Actual words: {actual_words} (variance: {variance:+d})")
        
        return story_data
    
    def _generate_narrative_story(self, topic: str, num_scenes: int = 10, words_per_scene: int = 15) -> Dict:
        """Generate a narrative story script with timing constraints.
        
        Args:
            topic: The content topic
            num_scenes: Target number of scenes (default 10)
            words_per_scene: Target words per scene for audio sync (default 15 = ~6 seconds)
        """
        
        total_words = num_scenes * words_per_scene
        
        prompt = f"""
        You are a MASTER STORYTELLER — the kind of narrator who makes 5th graders sit on the edge of their seats.
        You're about to tell a story that will be turned into a viral TikTok/Reels video.
        
        Your topic: {topic}
        
        🎭 YOUR STORYTELLING PERSONA:
        - You're like a campfire storyteller mixed with a documentary narrator
        - You speak with DRAMA, SUSPENSE, and EMOTION
        - You make listeners FEEL like they're IN the moment
        - You use simple words that EVERYONE can understand (5th grade level)
        - Every single word you choose is deliberate and powerful
        
        🔥 THE #1 RULE: DON'T RUSH THE GOOD PARTS!
        
        This is where most stories fail. When something AMAZING happens, you MUST:
        - BUILD UP the tension: What's at stake? Who's watching? What could go wrong?
        - PAINT THE SCENE: What does it look like? What are people thinking?
        - DELIVER THE MOMENT: Let the key action breathe. Make it feel EPIC.
        - SHOW THE REACTION: How did people respond? What did it mean?
        
        ❌ BAD (too rushed): "Marcus Aurelius forgave the slave who spilled oil on him."
        ✅ GOOD (dramatic): 
           Scene 1: "A slave's hand trembled. Hot oil splashed across the Emperor's robes."
           Scene 2: "The entire room went silent. Everyone held their breath."
           Scene 3: "All eyes locked on Marcus Aurelius. What would the most powerful man do?"
           Scene 4: "He looked at the terrified slave... and simply said: 'I'm sorry for getting in your way.'"
           Scene 5: "The crowd was stunned. This was the most powerful man in the world — and he apologized."
        
        See the difference? The GOOD version makes you FEEL it. You're THERE.
        
        📖 STORYTELLING TECHNIQUES TO USE:
        - Start scenes with ACTION or SENSORY details ("His hands shook...", "The crowd gasped...")
        - Use short, punchy sentences for IMPACT
        - Create CONTRAST (powerful vs humble, chaos vs calm, fear vs courage)
        - End scenes on MINI-CLIFFHANGERS when possible
        - Use phrases like "And then...", "But here's what nobody expected...", "What happened next changed everything..."
        - Make the listener CURIOUS about what comes next
        
        ⚠️ TIMING CONSTRAINT (MUST FOLLOW):
        - Each scene MUST have EXACTLY 12-15 words (creates 5-6 seconds of speech)
        - Total: {num_scenes} scenes × {words_per_scene} words = ~{total_words} words
        - COUNT YOUR WORDS. If a scene has <12 or >15 words, REWRITE IT.
        
        📝 STORY STRUCTURE:
        1. HOOK (scene 1): Start with ACTION or a BOLD promise. No slow intros.
           * GOOD: "A slave just ruined the Emperor's most expensive robe. Everyone froze."
           * BAD: "Today I want to tell you about Marcus Aurelius..."
        2. BUILD-UP (scenes 2-4): Set the stage. Who? Where? What's at stake?
        3. THE KEY MOMENT (scenes 5-7): This is the HEART of the story. DON'T RUSH IT.
           - Take time to describe WHAT happened
           - Show the TENSION and REACTIONS
           - Let the moment LAND with impact
        4. THE MEANING (scenes 8-9): Why does this matter? What's the lesson?
        5. OUTRO (scene {num_scenes}): Powerful final thought that sticks with them.
        
        Generate exactly {num_scenes} scenes.
        
        Format as VALID JSON:
        {{
            "script": "full narration text - the complete story",
            "scenes": [
                {{
                    "scene_number": 1,
                    "text": "portion of script for this scene - EXACTLY 12-15 WORDS",
                    "word_count": 14,
                    "target_duration": 6,
                    "visual_description": "vivid, specific image description (what we SEE in this moment)",
                    "slide_subject": "BOLD TEXT OVERLAY - 1-3 words max (e.g., 'THE EMPEROR', 'SILENCE')",
                    "key_concept": "main idea or emotion in this scene"
                }}
            ],
            "hook": "the attention-grabbing opening line",
            "climax_scenes": [5, 6, 7],
            "total_word_count": {total_words},
            "estimated_duration_seconds": {num_scenes * 6}
        }}
        
        SLIDE_SUBJECT EXAMPLES:
        - Action scenes: "THE FALL", "CHAOS", "THE CHOICE"
        - Character intro: "MARCUS AURELIUS", "THE SLAVE"
        - Emotional beats: "SILENCE", "FEAR", "HUMILITY"
        - Lessons: "TRUE POWER", "WISDOM", "THE TRUTH"
        
        Remember: You're not writing a Wikipedia article. You're telling a STORY that will make someone stop scrolling and FEEL something. Make every word count.
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
            story_data['content_type'] = 'story'
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
    
    def generate_mentor_slideshow(self, topic: str) -> Dict:
        """
        Generate a philosophical mentor-style slideshow script.
        
        Written in a direct, no-nonsense motivational tone using second person "you"
        with occasional first-person plural "we" for solidarity.
        
        Structure:
        - Slide 1: Hook (1 text item, 6-10 words, large font)
        - Slides 2-6: Three-part structure each:
            1. Short philosophical insight/mental trap (6-12 words, medium-large font)
            2. "What it does:" (3-6 words, small font)
            3. "Why it matters:" (10-20 words, small font)
        - Final slide: 2-3 text items:
            1. Rhetorical question/statement (6-10 words, medium font)
            2. Call to action (8-15 words, small font)
            3. Philosophical truth/encouragement (8-12 words, small font)
        """
        
        prompt = f"""
        You are a PHILOSOPHICAL MENTOR texting hard truths to someone ready to level up their thinking.
        
        Your topic: {topic}
        
        🎭 YOUR VOICE & PERSONA:
        - Direct, no-nonsense motivational tone
        - Second person "you" with occasional "we" for solidarity
        - 6th-7th grade reading level
        - You've walked the path of self-discovery — now sharing what ACTUALLY works
        - Short, punchy 5-10 word sentences mixed with occasional longer reflective statements
        - Rhetorical questions that challenge assumptions
        - Repetition of key philosophical concepts for emphasis
        - Direct callouts that make readers examine their own thinking patterns
        
        ✍️ WRITING STYLE:
        - Simple everyday words blended with accessible philosophical terminology
        - Periods for emphasis after short declarative statements
        - Occasional ellipses (...) for contemplative pauses
        - Questions to provoke self-reflection
        - Staccato and urgent when calling out mental traps
        - Calm and grounding when offering philosophical wisdom
        - Sentence fragments for impact
        - NO corporate speak — you're a philosophical coach who respects their intelligence
        - Occasional ALL CAPS for philosophical concepts or pivotal realizations
        - Concrete, relatable vocabulary translating ancient wisdom into modern struggles
        
        📱 MODERN STRUGGLES TO CONNECT TO:
        - Scrolling and distraction
        - Purpose and meaning
        - Self-awareness and growth
        - Comparison and insecurity
        - Overthinking and anxiety
        
        📝 SLIDE STRUCTURE (MUST FOLLOW EXACTLY):
        
        **SLIDE 1 — THE HOOK**
        - 1 text item only
        - 6-10 words MAXIMUM
        - Large font energy — this stops the scroll
        - Make it provocative, challenging, or deeply relatable
        - Examples: "Your mind is lying to you. Again.", "Nobody taught you how to think."
        
        **SLIDES 2-6 — THE CONTENT (5 slides total)**
        Each slide has EXACTLY 3 text items:
        
        1. **Main insight** (medium-large font): 6-12 words
           - A philosophical insight OR mental trap being called out
           - Direct, punchy, makes them pause
           - Examples: "You're chasing happiness. That's why you don't have it."
           
        2. **"What it does:"** (small font): 3-6 words
           - Brief label explaining the psychological mechanism
           - Start with "What it does:" then the explanation
           - Examples: "What it does: Keeps you stuck in loops."
           
        3. **"Why it matters:"** (small font): 10-20 words
           - Connects the insight to personal growth or philosophical understanding
           - Start with "Why it matters:" then the explanation
           - Examples: "Why it matters: When you stop chasing, you create space for peace to find you."
        
        **SLIDE 7 — THE OUTRO**
        2-3 text items:
        
        1. **Rhetorical question or statement** (medium font): 6-10 words
           - Challenges them to reflect
           - Examples: "What are you really running from?", "The work starts now."
           
        2. **Call to action** (small font): 8-15 words
           - Encourage saving, reflecting, or continuing the journey
           - Examples: "Save this. Read it again when your mind starts lying."
           
        3. **Philosophical truth** (small font, optional but recommended): 8-12 words
           - Encouraging or grounding final thought
           - Examples: "The truth was always inside you. You just forgot."
        
        🔥 EMOTIONAL ARC:
        - Start with CONFRONTATION (uncomfortable truths)
        - Move through RECOGNITION (they see themselves)
        - End with EMPOWERMENT (deeper understanding)
        
        ❌ DON'T:
        - Use corporate jargon ("leverage", "optimize", "synergy")
        - Be preachy or condescending
        - Use complex philosophical jargon without context
        - Make it feel like a lecture
        
        ✅ DO:
        - Make them feel SEEN
        - Challenge their assumptions
        - Use "you" frequently
        - Reference modern struggles (phones, scrolling, comparison)
        - Ground ancient wisdom in TODAY's problems
        
        📋 FORMAT AS VALID JSON:
        {{
            "title": "Short catchy title",
            "topic": "{topic}",
            "content_type": "mentor_slideshow",
            "writing_style": "philosophical_mentor",
            "total_slides": 7,
            "slides": [
                {{
                    "slide_number": 1,
                    "slide_type": "hook",
                    "text_items": [
                        {{
                            "text": "Your mind is lying to you. Again.",
                            "font_size": "large",
                            "word_count": 7
                        }}
                    ],
                    "visual_description": "Dark moody background with fractured mirror or distorted reflection, philosophical and introspective"
                }},
                {{
                    "slide_number": 2,
                    "slide_type": "content",
                    "text_items": [
                        {{
                            "text": "You scroll to escape. But escape from what?",
                            "font_size": "medium-large",
                            "word_count": 9
                        }},
                        {{
                            "label": "What it does:",
                            "text": "Numbs the real questions.",
                            "font_size": "small",
                            "word_count": 4
                        }},
                        {{
                            "label": "Why it matters:",
                            "text": "Every swipe is a vote against facing yourself. The phone isn't the problem — it's the hiding.",
                            "font_size": "small",
                            "word_count": 18
                        }}
                    ],
                    "visual_description": "Person illuminated only by phone screen in dark room, zombie-like glow, modern isolation"
                }},
                {{
                    "slide_number": 7,
                    "slide_type": "outro",
                    "text_items": [
                        {{
                            "text": "What will you choose to see?",
                            "font_size": "medium",
                            "word_count": 6
                        }},
                        {{
                            "text": "Save this. Come back when the fog rolls in.",
                            "font_size": "small",
                            "word_count": 10
                        }},
                        {{
                            "text": "Clarity was always there. You just stopped looking.",
                            "font_size": "small",
                            "word_count": 9
                        }}
                    ],
                    "visual_description": "Person standing at crossroads or doorway with light streaming through, choice and awakening"
                }}
            ]
        }}
        
        Generate EXACTLY 7 slides following this structure.
        Make it feel like a philosophical friend texting you hard truths at 2am.
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
            slideshow_data = json.loads(cleaned_text)
            slideshow_data['content_type'] = 'mentor_slideshow'
            return slideshow_data
            
        except Exception as e:
            print(f"Error generating mentor slideshow: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self.generate_mentor_slideshow(topic)
                except:
                    pass
            return None

    def generate_slideshow_script(self, topic: str) -> Dict:
        """
        Generate a slideshow script for children's-book-style slides.
        
        Each slide is one "page" of the story - easy to consume, spoon-fed.
        Supports TWO types of content:
        1. PERSON-BASED: "5 philosophers who..." -> Each slide = one person
        2. ARGUMENT-BASED: "Why X can't replace Y" -> Slide 0 = hook claim, each slide = one reason
        
        Returns structured data with slides containing:
        - slide_number (0 = hook, 1-N = content slides)
        - slide_type (hook, reason, person, quote, outro)
        - display_text (main text to show on slide)
        - subtitle (secondary text, e.g., reason explanation)
        - visual_description (for image generation)
        """
        
        prompt = f"""
        You are a VIRAL CONTENT CREATOR making TikTok slideshows that get MILLIONS of views.
        
        Your topic: {topic}
        
        🎭 YOUR #1 JOB: CREATE A THOUGHT-PROVOKING, CURIOSITY-INDUCING HOOK
        
        The FIRST SLIDE (slide 0) is EVERYTHING. It must:
        1. Make them STOP scrolling
        2. Make them CURIOUS about what's next
        3. Tie back to PHILOSOPHY (even indirectly)
        
        ⚠️ CRITICAL: ALWAYS CONNECT TO PHILOSOPHY
        
        We're promoting a philosophy app. Even when talking about modern figures (Steve Jobs, Elon Musk, Oprah),
        the hook should connect their success to PHILOSOPHICAL WISDOM or ANCIENT TEACHINGS.
        
        This creates curiosity: "Wait, Steve Jobs used ancient philosophy? I need to know more..."
        
        🔥 HOOK TRANSFORMATION EXAMPLES:
        
        ❌ BORING: "Business quotes from Steve Jobs"
        ❌ BETTER BUT NOT GREAT: "5 rules Steve Jobs lived by"
        ✅ PERFECT: "THE ANCIENT PHILOSOPHY STEVE JOBS SECRETLY LIVED BY"
        ✅ ALSO GOOD: "STEVE JOBS FOLLOWED ONE 2000-YEAR-OLD RULE HIS WHOLE LIFE"
        
        ❌ BORING: "Lessons from successful leaders"
        ✅ PERFECT: "5 LEADERS WHO SECRETLY FOLLOWED ANCIENT PHILOSOPHY"
        ✅ ALSO GOOD: "WHAT BILLIONAIRES LEARNED FROM DEAD PHILOSOPHERS"
        
        ❌ BORING: "Stoic principles for daily life"
        ✅ PERFECT: "THE STOIC SECRET THAT BUILT EMPIRES (AND STILL WORKS TODAY)"
        
        ❌ BORING: "Marcus Aurelius quotes"
        ✅ PERFECT: "A ROMAN EMPEROR'S DIARY THAT BILLIONAIRES READ EVERY MORNING"
        ✅ ALSO GOOD: "THE 2000-YEAR-OLD JOURNAL ENTRY THAT CHANGED EVERYTHING"
        
        ❌ BORING: "Why philosophy matters"
        ✅ PERFECT: "THE ONE QUESTION SCIENCE WILL NEVER ANSWER"
        ✅ ALSO GOOD: "WHAT EVERY GENIUS EVENTUALLY DISCOVERED"
        
        📋 HOOK FORMULAS THAT CREATE CURIOSITY + TIE TO PHILOSOPHY:
        
        1. "[MODERN SUCCESS] + [ANCIENT WISDOM]"
           → "THE ANCIENT PHILOSOPHY STEVE JOBS SECRETLY LIVED BY"
           → "WHAT BILLIONAIRES LEARNED FROM DEAD PHILOSOPHERS"
           → "THE 2000-YEAR-OLD RULE ELON MUSK FOLLOWS"
        
        2. "[PROVOCATIVE QUESTION/CLAIM]"
           → "THE ONE QUESTION SCIENCE WILL NEVER ANSWER"
           → "WHAT THEY DON'T TEACH YOU IN SCHOOL (BUT SHOULD)"
           → "WHY THE SMARTEST PEOPLE READ ANCIENT BOOKS"
        
        3. "[MYSTERY + REVELATION]"
           → "THE SECRET PHILOSOPHERS KNEW 2000 YEARS AGO"
           → "THEY KNEW THE ANSWER BEFORE WE ASKED THE QUESTION"
           → "A ROMAN EMPEROR'S DIARY THAT CHANGED MODERN LEADERSHIP"
        
        4. "[DRAMATIC CONTRAST]"
           → "HE RULED AN EMPIRE BUT ASKED ONE SIMPLE QUESTION EVERY NIGHT"
           → "THEY KILLED HIM FOR ASKING QUESTIONS"
           → "HE HAD EVERYTHING. HE GAVE IT ALL UP FOR ONE IDEA."
        
        🎯 HOOK SLIDE RULES:
        - MUST be 5-15 words (short enough to read instantly)
        - ALL CAPS
        - NO subtitle on hook slide — let it breathe
        - MUST create CURIOSITY ("wait, what? I need to know more...")
        - MUST tie to PHILOSOPHY (even indirectly: "ancient wisdom", "2000 years old", "what philosophers knew")
        - Make the viewer think: "I didn't know philosophy was connected to this..."
        
        📖 CONTENT SLIDES (slides 1-N):
        Each slide after the hook is ONE piece of content (one lesson, one reason, one person).
        
        ⚠️ IMPORTANT: Always tie content back to PHILOSOPHICAL WISDOM
        
        Even when talking about modern people, connect their success to philosophical principles:
        - Steve Jobs → Connect to Zen Buddhism, simplicity philosophy, "focus" wisdom
        - Elon Musk → Connect to first principles thinking (Aristotle), Stoic persistence
        - Oprah → Connect to Stoic resilience, growth mindset philosophy
        - Any successful person → What ancient philosophical principle did they embody?
        
        **FOR MODERN FIGURES:**
        Don't just share their quote — reveal the philosophical PRINCIPLE behind it:
        - "Steve Jobs followed the Zen principle: 'Simplicity is the ultimate sophistication.'"
        - "Elon Musk uses Aristotle's 'first principles' — break everything down to its core truth."
        - "Oprah lives by the Stoic teaching: 'The obstacle is the way.'"
        
        **FOR ANCIENT PHILOSOPHERS:**
        Make their wisdom feel RELEVANT to today:
        - "Marcus Aurelius wrote this 2000 years ago. CEOs still read it every morning."
        - "Socrates asked questions so dangerous, they killed him. These questions still matter."
        
        **FOR LESSONS/ARGUMENTS:**
        Connect abstract ideas to concrete impact:
        - "This one principle built empires — and it still works in 2024."
        
        🔥 SUBTITLE FORMULAS (for content slides):
        
        ❌ BAD: "Steve Jobs valued simplicity."
        ✅ GOOD: "He followed one Zen principle: 'Simplicity is the ultimate sophistication.'"
        
        ❌ BAD: "Marcus Aurelius practiced controlling his emotions."
        ✅ GOOD: "He ruled Rome. Every night he asked: 'Was I good today?' CEOs still do this."
        
        ❌ BAD: "Philosophy asks different questions than science."
        ✅ GOOD: "Science tells you HOW fire burns. Philosophy asks if you should light the match."
        
        ❌ BAD: "Elon Musk works hard."
        ✅ GOOD: "He uses Aristotle's 'first principles' — question EVERYTHING until you find the truth."
        
        SUBTITLE RULES:
        - 8-18 words max
        - Use CONTRAST ("He ruled Rome... but asked if he was good")
        - Use DRAMA ("they killed him", "brutal truth", "changed everything")
        - TIE TO PHILOSOPHY ("ancient principle", "2000 years old", "philosophers knew")
        - Make it FEEL RELEVANT ("CEOs still do this", "still works today")
        
        📝 FINAL STRUCTURE:
        1. HOOK (slide 0): Thought-provoking, curiosity-inducing, tied to philosophy (5-15 words, ALL CAPS, no subtitle)
        2. CONTENT (slides 1-4): One lesson/reason/person per slide, each tied back to philosophical wisdom
        3. OUTRO (slide 5): Challenge them to THINK DEEPER or EXPLORE MORE
        
        🎬 OUTRO SLIDE FORMULAS (create desire to learn more philosophy):
        
        ✅ GOOD OUTROS:
        - "ANCIENT WISDOM. MODERN POWER." (subtitle: "Which philosophy will you live by?")
        - "2000 YEARS OF WISDOM" (subtitle: "Are you ready to listen?")
        - "THE QUESTION REMAINS" (subtitle: "What philosophy will guide YOUR life?")
        - "THEY KNEW THE ANSWERS" (subtitle: "Now it's your turn to ask the questions.")
        - "PHILOSOPHY ISN'T DEAD" (subtitle: "It's hiding in everything you admire.")
        
        The outro should make them think: "I want to learn more about philosophy..."
        
        REQUIREMENTS:
        - display_text: 2-6 words max (ALL CAPS)
        - subtitle: 8-15 words (punchy, memorable, emotional)
        - visual_description: MUST match the slide subject (see rules below)
        - Total slides: 5-7
        
        🎨 VISUAL DESCRIPTION RULES (CRITICAL):
        
        The background image MUST visually represent WHAT THE SLIDE IS ABOUT.
        
        Think: "What image would make sense behind this text?"
        
        ✅ GOOD EXAMPLES:
        
        Slide about STEVE JOBS:
        - display_text: "STEVE JOBS"
        - subtitle: "He started in a garage. His rule? 'Don't waste time living someone else's life.'"
        - visual_description: "Steve Jobs silhouette in black turtleneck, minimalist white/gray background, holding glowing Apple logo or lightbulb, clean iconic aesthetic"
        
        Slide about MARCUS AURELIUS:
        - display_text: "MARCUS AURELIUS"  
        - subtitle: "He ruled Rome. Every night he asked: 'Was I good today?'"
        - visual_description: "Roman emperor in purple robes writing in journal by candlelight, marble columns, warm golden lighting, classical oil painting style"
        
        Slide about ELON MUSK:
        - display_text: "ELON MUSK"
        - subtitle: "He risked his entire fortune. Three times."
        - visual_description: "Silhouette of man against rocket launch, SpaceX-style imagery, dramatic orange and black, futuristic and bold"
        
        Slide about A LESSON (not a person):
        - display_text: "LESSON #1"
        - subtitle: "Control what you can. Ignore what you can't."
        - visual_description: "Hands releasing scattered papers into the wind, letting go, peaceful sky background, minimalist and freeing"
        
        Slide about WHY PHILOSOPHY MATTERS:
        - display_text: "THE BLIND SPOT"
        - subtitle: "Science tells you HOW. Philosophy asks WHY."
        - visual_description: "Split image: cold blue scientific lab on left, warm golden ancient library on right, contrast between logic and wisdom"
        
        ❌ BAD EXAMPLES (DON'T DO THIS):
        
        - Slide about Steve Jobs but visual says "ancient philosopher in robes" ❌
        - Slide about a lesson but visual says "generic dark background" ❌
        - Slide about Elon Musk but visual says "classical Greek statue" ❌
        
        VISUAL DESCRIPTION FORMULA:
        1. WHO or WHAT is this slide about? → Show THAT person/concept
        2. What's the MOOD? → Match the emotional tone (inspiring, dramatic, peaceful)
        3. Keep it SIMPLE → One clear image, not cluttered
        4. Make it AESTHETIC → Dark/moody OR clean/minimalist, TikTok-worthy
        
        Format as VALID JSON:
        {{
            "title": "Short catchy title",
            "topic": "{topic}",
            "content_type": "lessons" or "argument" or "person_list",
            "total_slides": 6,
            "slides": [
                {{
                    "slide_number": 0,
                    "slide_type": "hook",
                    "display_text": "5 LEADERS WHOSE RULES CHANGED EVERYTHING",
                    "subtitle": "",
                    "visual_description": "Dramatic montage silhouettes of iconic leaders, dark moody background with golden light rays, powerful and epic atmosphere"
                }},
                {{
                    "slide_number": 1,
                    "slide_type": "person",
                    "display_text": "STEVE JOBS",
                    "subtitle": "He started in a garage. His rule? 'Don't waste time living someone else's life.'",
                    "visual_description": "Steve Jobs silhouette in signature black turtleneck, minimalist white background, holding glowing lightbulb, clean and iconic"
                }},
                {{
                    "slide_number": 2,
                    "slide_type": "person",
                    "display_text": "MARCUS AURELIUS",
                    "subtitle": "He ruled Rome. Every night he wrote: 'Was I good today?'",
                    "visual_description": "Roman emperor in purple robes writing in leather journal by candlelight, marble columns in shadows, warm golden intimate lighting"
                }},
                {{
                    "slide_number": 3,
                    "slide_type": "person",
                    "display_text": "OPRAH WINFREY",
                    "subtitle": "Born in poverty. Her rule? 'Turn your wounds into wisdom.'",
                    "visual_description": "Powerful woman silhouette on stage with bright spotlight behind her, audience in darkness, triumphant and inspiring"
                }},
                {{
                    "slide_number": 4,
                    "slide_type": "outro",
                    "display_text": "WHAT'S YOUR RULE?",
                    "subtitle": "The one you'll live by... starting today.",
                    "visual_description": "Person silhouette standing at sunrise on mountaintop, new beginning vibes, golden hour, inspiring and hopeful"
                }}
            ]
        }}
        
        Remember: 
        1. The HOOK is EVERYTHING — transform the topic into a scroll-stopper
        2. The VISUAL must MATCH the slide subject — Steve Jobs = Steve Jobs imagery, not generic philosopher
        3. Keep visuals SIMPLE and AESTHETIC — one clear concept per image
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
            slideshow_data = json.loads(cleaned_text)
            slideshow_data['content_type'] = 'slideshow'
            return slideshow_data
            
        except Exception as e:
            print(f"Error generating slideshow script: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self.generate_slideshow_script(topic)
                except:
                    pass
            return None

    def generate_wisdom_slideshow(self, topic: str, user_prompt: str = None) -> Dict:
        """
        Generate a philosophical wisdom slideshow script with the PhilosophizeMe style.

        This is the MAIN generation method for the app frontend. It follows a specific structure:
        - Slide 1: Hook (15-20 words) - sets the tone for the whole slideshow
        - Slides 2-5: Numbered philosophical insights (40-70 words each)
        - Slide 6: CTA for PhilosophizeMe app

        Written in thoughtful, introspective tone, 8th grade reading level, wise mentor style.
        Uses second-person perspective with numbered points and short, impactful sentences.

        Args:
            topic: The main topic/concept for the slideshow
            user_prompt: Optional user-provided prompt to enhance (we build off weak prompts)
        """

        # Build the enhanced topic from user input
        enhanced_topic = topic
        if user_prompt:
            enhanced_topic = f"{topic} - {user_prompt}"

        prompt = f"""
        You are a WISE PHILOSOPHICAL MENTOR creating a slideshow that will change how people think.

        Your topic: {enhanced_topic}

        🎭 YOUR VOICE & PERSONA:
        Write in a thoughtful, introspective tone using second-person perspective ("you").
        Write at an 8th grade reading level in a style that sounds like a wise mentor sharing hard-earned wisdom with a curious student.
        Position yourself as someone who has walked the philosophical path and is gently guiding others.

        ✍️ WRITING STYLE (CRITICAL - FOLLOW EXACTLY):
        - Use a mix of short declarative sentences (5-7 words) and thought-provoking questions
        - Create moments of reflection through intentional spacing and line breaks
        - Blend therapy-influenced language about growth, awareness, and inner work with accessible philosophical terminology
        - Use periods for definitive statements
        - Use questions to prompt introspection
        - The writing should flow like a thoughtful conversation with natural pauses
        - Each idea should land before moving to the next

        📝 SLIDE STRUCTURE (MUST FOLLOW EXACTLY):

        **SLIDE 1 — THE HOOK** (Sets the tone for EVERYTHING)
        - 15-20 words EXACTLY
        - Large font energy — this is the title slide
        - Must introduce a numbered list of philosophical insights OR realizations
        - Sets the introspective, wisdom-sharing tone
        - Examples:
          * "5 truths about yourself you've been avoiding. Each one will set you free."
          * "3 lies your mind tells you every day. And how the Stoics fought back."
          * "The 4 questions that changed everything I thought I knew about happiness."

        **SLIDES 2-5 — THE NUMBERED INSIGHTS (4 slides)**
        Each slide contains ONE numbered point from your list:
        - 40-70 words per slide
        - Start with a BOLD statement that captures the insight
        - Follow with a deeper explanation connecting ancient wisdom to modern self-understanding
        - Use intentional line breaks to create reading rhythm
        - Make each point feel like a revelation

        FORMAT for content slides:
        ```
        [NUMBER]. [BOLD INSIGHT STATEMENT]

        [Deeper explanation with line breaks]
        [Connect to personal growth]
        [End with reflection or question]
        ```

        **SLIDE 6 — THE CALL TO ACTION**
        EXACTLY this text (do not change):
        "Want to learn philosophy in practice?

        Download PhilosophizeMe on the App Store.

        It's free."

        🔥 EMOTIONAL ARC:
        - Slide 1: Create CURIOSITY (what are these insights?)
        - Slides 2-3: Build RECOGNITION (they see themselves)
        - Slides 4-5: Offer TRANSFORMATION (new perspective)
        - Slide 6: Invite CONTINUATION (download the app)

        📖 EXAMPLE OUTPUT QUALITY:

        **Hook example:**
        "4 mental traps that keep you stuck.

        Ancient philosophers knew about every one of them.

        And they knew the way out."

        **Content slide example:**
        "1. You think you need to be certain before you act.

        But certainty is the enemy of growth.

        The Stoics taught that action creates clarity.
        Not the other way around.

        What would you do today if you didn't need to know how it ends?"

        ❌ DON'T:
        - Use corporate jargon or buzzwords
        - Be preachy, condescending, or lecture-like
        - Use complex philosophical terms without context
        - Rush through ideas — let each one breathe
        - Forget the line breaks for reading rhythm

        ✅ DO:
        - Make them feel SEEN and understood
        - Use "you" frequently — this is personal
        - Connect ancient wisdom to TODAY's struggles
        - Create space for reflection between ideas
        - Sound like a wise friend, not a professor

        📋 FORMAT AS VALID JSON:
        {{
            "title": "Short catchy title for the slideshow",
            "topic": "{topic}",
            "content_type": "wisdom_slideshow",
            "writing_style": "philosophical_mentor",
            "total_slides": 6,
            "slides": [
                {{
                    "slide_number": 1,
                    "slide_type": "hook",
                    "title": "THE HOOK TITLE (2-5 words, ALL CAPS)",
                    "content": "The full 15-20 word hook text with line breaks",
                    "word_count": 18,
                    "visual_description": "Dark, moody philosophical background that matches the introspective tone"
                }},
                {{
                    "slide_number": 2,
                    "slide_type": "insight",
                    "title": "INSIGHT 1",
                    "content": "1. [Bold statement]\\n\\n[Deeper explanation with line breaks for rhythm]\\n\\n[Reflection or question]",
                    "word_count": 55,
                    "visual_description": "Background that matches the specific insight being shared"
                }},
                {{
                    "slide_number": 3,
                    "slide_type": "insight",
                    "title": "INSIGHT 2",
                    "content": "2. [Bold statement]\\n\\n[Deeper explanation]...",
                    "word_count": 50,
                    "visual_description": "..."
                }},
                {{
                    "slide_number": 4,
                    "slide_type": "insight",
                    "title": "INSIGHT 3",
                    "content": "3. [Bold statement]\\n\\n[Deeper explanation]...",
                    "word_count": 48,
                    "visual_description": "..."
                }},
                {{
                    "slide_number": 5,
                    "slide_type": "insight",
                    "title": "INSIGHT 4",
                    "content": "4. [Bold statement]\\n\\n[Deeper explanation]...",
                    "word_count": 52,
                    "visual_description": "..."
                }},
                {{
                    "slide_number": 6,
                    "slide_type": "cta",
                    "title": "PHILOSOPHIZE ME",
                    "content": "Want to learn philosophy in practice?\\n\\nDownload PhilosophizeMe on the App Store.\\n\\nIt's free.",
                    "word_count": 15,
                    "visual_description": "Clean, minimal background with subtle philosophical imagery, app-promotional feel"
                }}
            ]
        }}

        Generate EXACTLY 6 slides following this structure.
        Make it feel like wisdom being shared from one soul to another.
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
            slideshow_data = json.loads(cleaned_text)
            slideshow_data['content_type'] = 'wisdom_slideshow'
            return slideshow_data

        except Exception as e:
            print(f"Error generating wisdom slideshow: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self.generate_wisdom_slideshow(topic, user_prompt)
                except:
                    pass
            return None

    def generate_script(self, topic: str, content_type: str) -> Optional[Dict]:
        """
        Generate a script using the centralized prompt configuration.

        This is the MAIN entry point for script generation. It uses the
        prompt_config.py templates for consistent, high-quality output.

        Args:
            topic: The topic to generate content about
            content_type: One of: list_educational, list_existential, wisdom_slideshow, narrative_story

        Returns:
            Dict with script data including slides, or None on failure
        """
        # Get the prompt template for this content type
        prompt = get_script_prompt(topic, content_type)
        config = get_content_type_config(content_type)

        print(f"\n🎬 Generating {content_type} script for: {topic}")
        print(f"   Using {config.num_slides} slides, {config.slide_structure} structure")

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
            script_data = json.loads(cleaned_text)

            # Ensure content_type is set
            script_data['content_type'] = content_type
            script_data['default_image_style'] = config.default_image_style

            print(f"✅ Generated {len(script_data.get('slides', []))} slides")
            return script_data

        except Exception as e:
            print(f"Error generating script: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Model not found, trying gemini-2.0-flash-exp...")
                try:
                    self.text_model_name = 'gemini-2.0-flash-exp'
                    return self.generate_script(topic, content_type)
                except:
                    pass
            return None

    def enhance_topic_prompt(self, raw_topic: str) -> str:
        """
        Enhance a weak/basic topic into a more compelling prompt.

        The backend should take what the user puts in and build off of it,
        assuming user prompts might be weak or incomplete.

        Args:
            raw_topic: The user's raw input topic

        Returns:
            An enhanced, more specific topic string
        """

        prompt = f"""
        You are a content strategist who helps transform basic topic ideas into compelling slideshow concepts.

        The user has provided this topic: "{raw_topic}"

        Your job is to enhance this into a more specific, engaging topic that:
        1. Has a clear angle or perspective
        2. Creates curiosity
        3. Connects to universal human experiences
        4. Is suitable for a philosophical wisdom slideshow

        Examples of enhancement:
        - "stoicism" → "5 Stoic truths that will change how you handle stress"
        - "happiness" → "Why chasing happiness keeps you unhappy (and what to do instead)"
        - "anxiety" → "3 ancient techniques for calming an anxious mind"
        - "productivity" → "The philosophical reason you procrastinate (it's not laziness)"
        - "relationships" → "What the Stoics knew about love that we've forgotten"

        Return ONLY the enhanced topic string, nothing else.
        Keep it under 15 words.
        Make it specific and intriguing.
        """

        try:
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=prompt
            )

            if response.text:
                return response.text.strip().strip('"')
            return raw_topic

        except Exception as e:
            print(f"Error enhancing topic: {e}")
            return raw_topic

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
    
    # Test content type detection
    test_topics = [
        "Plato's Cave Allegory",           # story
        "5 philosophers who changed the world",  # list
        "Top 10 Stoic quotes",             # list
        "The founding of Stoicism",        # story
        "5 quotes from Marcus Aurelius",   # list
        "Nietzsche's Eternal Recurrence",  # story
    ]
    
    print("=== Content Type Detection Test ===")
    for topic in test_topics:
        content_type = handler._detect_content_type(topic)
        print(f"  '{topic}' -> {content_type}")
    
    print("\n=== Generating Sample Content ===")
    # Generate a list-style example
    story = handler.generate_philosophy_story("5 philosophers with powerful quotes")
    if story:
        print(f"\nGenerated Content (type: {story.get('content_type', 'unknown')}):")
        print(json.dumps(story, indent=2))
    else:
        print("Failed to generate story")