"""
Centralized Prompt Configuration for Philosophy Video Generator

This file contains all prompt templates organized by:
1. Content Types - determines script structure
2. Image Styles - determines visual aesthetic

Content Types:
- list_educational: "5 Philosophers who..." - distinct historical figures/concepts
- list_existential: "5 ways your mind evolves" - personal growth, abstract
- wisdom_slideshow: "4 truths about..." - numbered insights, introspective
- narrative_story: "The day Socrates died" - sequential storytelling

Image Styles:
- classical: Caravaggio, oil paintings, Renaissance masters
- surreal: Dalí-inspired, dreamlike, abstract
- cinematic: Movie poster, dramatic lighting, dark
- minimal: Clean, modern, geometric, simple
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


# =============================================================================
# CONTENT TYPE CONFIGURATIONS
# =============================================================================

@dataclass
class ContentTypeConfig:
    """Configuration for a content type."""
    id: str
    name: str
    description: str
    example: str
    default_image_style: str
    num_slides: int
    hook_style: str  # "bold_statement", "question", "dramatic"
    slide_structure: str  # "distinct_subjects", "flowing_abstract", "numbered_insights"


CONTENT_TYPES: Dict[str, ContentTypeConfig] = {
    "list_educational": ContentTypeConfig(
        id="list_educational",
        name="List - Educational",
        description="Historical figures, schools of thought, factual lists",
        example="5 Stoic philosophers who changed history",
        default_image_style="classical",
        num_slides=6,
        hook_style="bold_statement",
        slide_structure="distinct_subjects"
    ),
    "list_existential": ContentTypeConfig(
        id="list_existential",
        name="List - Existential",
        description="Personal growth, self-reflection, abstract concepts",
        example="5 ways your mind is evolving right now",
        default_image_style="surreal",
        num_slides=6,
        hook_style="question",
        slide_structure="flowing_abstract"
    ),
    "wisdom_slideshow": ContentTypeConfig(
        id="wisdom_slideshow",
        name="Wisdom Slideshow",
        description="Numbered insights, mentor tone, introspective",
        example="4 truths about yourself you've been avoiding",
        default_image_style="cinematic",
        num_slides=6,
        hook_style="dramatic",
        slide_structure="numbered_insights"
    ),
    "narrative_story": ContentTypeConfig(
        id="narrative_story",
        name="Narrative Story",
        description="Sequential storytelling, dramatic arc, cohesive visuals",
        example="The day Socrates chose death over silence",
        default_image_style="cinematic",
        num_slides=8,
        hook_style="dramatic",
        slide_structure="sequential_scenes"
    ),
}


# =============================================================================
# IMAGE STYLE CONFIGURATIONS
# =============================================================================

@dataclass
class ImageStyleConfig:
    """Configuration for an image style."""
    id: str
    name: str
    description: str
    preview_keywords: str  # For generating preview thumbnails
    hook_prompt: str  # Special prompt for hook/first slide
    content_prompt: str  # Prompt for content slides
    outro_prompt: str  # Prompt for final slide
    negative_prompt: str  # What to avoid


IMAGE_STYLES: Dict[str, ImageStyleConfig] = {
    "classical": ImageStyleConfig(
        id="classical",
        name="Classical",
        description="Renaissance oil paintings, Caravaggio lighting",
        preview_keywords="classical oil painting philosopher",
        hook_prompt="""ARTISTIC STYLE:
- Classical oil painting in the style of Caravaggio and Rembrandt
- Dramatic chiaroscuro lighting with deep shadows and golden highlights
- Rich Renaissance color palette: burgundy, gold, deep blue, amber
- Baroque composition with dramatic poses
- Museum-quality fine art aesthetic
- Textured brushstrokes visible

MOOD: Timeless, authoritative, historically significant""",
        content_prompt="""ARTISTIC STYLE:
- Classical oil painting, Renaissance masters style
- Dramatic Caravaggio chiaroscuro lighting
- Rich deep colors: burgundy, gold, deep blue
- Mysterious shadows with warm golden highlights
- Fine art museum quality
- Historical gravitas

COMPOSITION:
- Subject prominently featured
- Dark moody background
- Center area slightly clear for text overlay""",
        outro_prompt="""ARTISTIC STYLE:
- Classical oil painting style
- Contemplative, reflective mood
- Soft golden light suggesting wisdom/enlightenment
- Single figure or symbolic object
- Inviting, warm atmosphere""",
        negative_prompt="modern elements, technology, bright neon colors, cartoon style, anime, text, words, letters"
    ),

    "surreal": ImageStyleConfig(
        id="surreal",
        name="Surreal",
        description="Dreamlike, Dalí-inspired, abstract and flowing",
        preview_keywords="surreal dreamlike abstract mind",
        hook_prompt="""ARTISTIC STYLE:
- Surrealist art inspired by Salvador Dalí and René Magritte
- Dreamlike, impossible landscapes
- Melting, morphing forms
- Ethereal color palette: deep purples, cosmic blues, soft pinks
- Floating elements defying gravity
- Symbolic imagery from the subconscious

MOOD: Mysterious, introspective, mind-expanding""",
        content_prompt="""ARTISTIC STYLE:
- Surrealist dreamscape
- Abstract, flowing forms
- Ethereal and otherworldly
- Colors: deep purple, cosmic blue, soft gold, rose
- Elements that morph and blend into each other
- Symbolic, psychological imagery

COMPOSITION:
- Abstract representation of the concept
- Dreamlike transitions between elements
- Soft focus areas for text overlay""",
        outro_prompt="""ARTISTIC STYLE:
- Surrealist style
- Sense of awakening or emergence
- Light breaking through abstract forms
- Hopeful, transcendent mood
- Gateway or portal imagery""",
        negative_prompt="realistic, photographic, harsh lines, corporate, sterile, text, words, letters"
    ),

    "cinematic": ImageStyleConfig(
        id="cinematic",
        name="Cinematic",
        description="Movie poster aesthetic, dramatic and bold",
        preview_keywords="cinematic dramatic movie poster dark",
        hook_prompt="""ARTISTIC STYLE:
- Cinematic movie poster aesthetic
- Dramatic teal and orange color grading
- High contrast with deep blacks and bright highlights
- Epic scale and composition
- Lens flare and atmospheric effects
- Bold, impactful visual storytelling

MOOD: Epic, intense, emotionally charged""",
        content_prompt="""ARTISTIC STYLE:
- Cinematic quality, film still aesthetic
- Dramatic lighting with strong contrast
- Color grading: teal shadows, orange highlights
- Atmospheric haze or particles
- Depth of field with bokeh
- Movie poster composition

COMPOSITION:
- Strong focal point
- Dramatic negative space
- Clear area in center for text""",
        outro_prompt="""ARTISTIC STYLE:
- Cinematic, hopeful ending scene
- Dawn or golden hour lighting
- Silhouette or backlit subject
- Sense of journey completion
- Inspirational, forward-looking""",
        negative_prompt="flat lighting, amateur, snapshot, bright daylight, cartoon, text, words, letters"
    ),

    "minimal": ImageStyleConfig(
        id="minimal",
        name="Minimal",
        description="Clean, modern, geometric shapes",
        preview_keywords="minimal modern geometric clean",
        hook_prompt="""ARTISTIC STYLE:
- Minimalist modern design
- Clean geometric shapes
- Limited color palette: black, white, one accent color
- Strong use of negative space
- Contemporary art gallery aesthetic
- Bold, simple forms

MOOD: Clean, focused, contemporary""",
        content_prompt="""ARTISTIC STYLE:
- Minimalist, modern aesthetic
- Simple geometric forms
- Monochromatic with one accent color
- Lots of negative space
- Clean lines, no clutter
- Abstract representation

COMPOSITION:
- Single focal element
- Generous whitespace/dark space
- Perfect for text overlay""",
        outro_prompt="""ARTISTIC STYLE:
- Minimalist style
- Single powerful symbol or shape
- Peaceful, resolved feeling
- Clean and memorable
- Iconic simplicity""",
        negative_prompt="cluttered, busy, realistic, detailed textures, ornate, baroque, text, words, letters"
    ),
}


# =============================================================================
# SCRIPT GENERATION PROMPTS
# =============================================================================

SCRIPT_PROMPTS = {
    "list_educational": """
You are creating a LIST-STYLE educational slideshow about historical/factual content.

TOPIC: {topic}

STRUCTURE (6 slides total):
- Slide 1 (HOOK): Bold statement introducing the list. 15-20 words. Sets authoritative tone.
- Slides 2-5 (CONTENT): Each slide features ONE distinct item from the list (person, concept, school of thought)
- Slide 6 (CTA): "Want to learn philosophy in practice? Download PhilosophizeMe on the App Store. It's free."

WRITING STYLE:
- Authoritative, educational tone
- Present tense, active voice
- Each item gets: Name/Title + Key fact + Why it matters
- 40-60 words per content slide
- Bold, memorable statements

VISUAL DESCRIPTIONS (CRITICAL):
- Hook: Dramatic overview image representing the theme
- Each content slide: SPECIFIC visual of that particular person/concept
  - If about Socrates: describe Socrates specifically
  - If about Stoicism: describe Stoic imagery specifically
- Each slide's visual should be DISTINCT from others

Example hook: "5 philosophers whose ideas still control how you think. You've never heard of some of them."

OUTPUT AS JSON:
{{
    "title": "Short title",
    "topic": "{topic}",
    "content_type": "list_educational",
    "total_slides": 6,
    "slides": [
        {{
            "slide_number": 1,
            "slide_type": "hook",
            "title": "HOOK TITLE",
            "content": "The hook text...",
            "visual_description": "Specific visual for hook that captures the list theme"
        }},
        {{
            "slide_number": 2,
            "slide_type": "list_item",
            "title": "ITEM NAME",
            "content": "1. [Item name]\\n\\n[Key information]\\n\\n[Why it matters]",
            "visual_description": "SPECIFIC visual of THIS particular item - describe exactly what/who should appear"
        }},
        // ... more slides
    ]
}}
""",

    "list_existential": """
You are creating an EXISTENTIAL/INTROSPECTIVE slideshow about personal growth and self-reflection.

TOPIC: {topic}

STRUCTURE (6 slides total):
- Slide 1 (HOOK): Thought-provoking question or realization. 15-20 words. Creates curiosity.
- Slides 2-5 (CONTENT): Each slide explores ONE aspect of the internal journey
- Slide 6 (CTA): "Want to learn philosophy in practice? Download PhilosophizeMe on the App Store. It's free."

WRITING STYLE:
- Second-person ("you") perspective
- Introspective, therapy-influenced language
- Mix of short statements (5-7 words) and deeper reflections
- Questions that prompt self-examination
- 40-70 words per content slide
- Intentional line breaks for reading rhythm

VISUAL DESCRIPTIONS (CRITICAL - ABSTRACT/SURREAL):
- Hook: Abstract imagery representing internal awakening or questioning
- Content slides: SURREAL, ABSTRACT visuals - NOT literal interpretations
  - Use metaphors: mirrors, doors, paths, light/shadow, water, birds, keys
  - Flowing, dreamlike imagery
  - Psychological/emotional symbolism
- Visuals should FLOW together as a cohesive journey

Example hook: "5 signs your mind is trying to tell you something. Most people ignore all of them."

OUTPUT AS JSON:
{{
    "title": "Short title",
    "topic": "{topic}",
    "content_type": "list_existential",
    "total_slides": 6,
    "slides": [
        {{
            "slide_number": 1,
            "slide_type": "hook",
            "title": "HOOK TITLE",
            "content": "The hook text...",
            "visual_description": "Abstract/surreal visual - e.g., 'A person standing before infinite mirrors reflecting different versions of themselves'"
        }},
        {{
            "slide_number": 2,
            "slide_type": "insight",
            "title": "INSIGHT TITLE",
            "content": "1. [Insight]\\n\\n[Deeper exploration]\\n\\n[Reflection question]",
            "visual_description": "Surreal abstract visual representing THIS specific insight - use metaphorical imagery"
        }},
        // ... more slides
    ]
}}
""",

    "wisdom_slideshow": """
You are a WISE PHILOSOPHICAL MENTOR creating a slideshow that will change how people think.

TOPIC: {topic}

STRUCTURE (6 slides total):
- Slide 1 (HOOK): Bold title introducing numbered insights. 15-20 words. Sets introspective tone.
- Slides 2-5 (INSIGHTS): Each slide contains ONE numbered philosophical insight
- Slide 6 (CTA): EXACTLY: "Want to learn philosophy in practice? Download PhilosophizeMe on the App Store. It's free."

WRITING STYLE:
- Thoughtful, introspective tone using second-person ("you")
- 8th grade reading level
- Wise mentor sharing hard-earned wisdom with a curious student
- Mix of short declarative sentences (5-7 words) and thought-provoking questions
- Therapy-influenced language about growth, awareness, inner work
- Intentional line breaks create reading rhythm
- 40-70 words per content slide

VISUAL DESCRIPTIONS:
- Each slide needs a SPECIFIC visual that matches its content
- Use metaphorical, atmospheric imagery
- Dark, moody, contemplative aesthetic
- Abstract representations of psychological concepts

Example hook: "4 mental traps that keep you stuck. Ancient philosophers knew every one of them."

OUTPUT AS JSON:
{{
    "title": "Short title",
    "topic": "{topic}",
    "content_type": "wisdom_slideshow",
    "total_slides": 6,
    "slides": [
        {{
            "slide_number": 1,
            "slide_type": "hook",
            "title": "HOOK TITLE",
            "content": "The full hook text with line breaks...",
            "visual_description": "Atmospheric visual setting the contemplative mood"
        }},
        {{
            "slide_number": 2,
            "slide_type": "insight",
            "title": "INSIGHT 1",
            "content": "1. [Bold statement]\\n\\n[Deeper explanation]\\n\\n[Reflection or question]",
            "visual_description": "Visual metaphor for THIS specific insight"
        }},
        // ... more slides
    ]
}}
""",

    "narrative_story": """
You are a LEGENDARY STORYTELLER creating a compelling philosophical narrative.

TOPIC: {topic}

STRUCTURE (8 slides total):
- Slide 1 (HOOK): Dramatic opening that pulls viewers in. 12-15 words.
- Slides 2-3 (SETUP): Establish the scene, introduce the philosopher/situation
- Slides 4-5 (RISING ACTION): Build tension, the challenge or conflict
- Slides 6-7 (CLIMAX & RESOLUTION): The key moment and its meaning
- Slide 8 (CTA): "Want to learn philosophy in practice? Download PhilosophizeMe on the App Store. It's free."

WRITING STYLE:
- Dramatic, cinematic storytelling
- Present tense for immediacy
- Short, punchy sentences (12-15 words per scene)
- Build emotional tension
- End with powerful insight

VISUAL DESCRIPTIONS (CRITICAL - SEQUENTIAL & COHESIVE):
- All images should feel like they're from the SAME MOVIE
- Consistent characters, settings, lighting across scenes
- Each scene builds visually on the previous
- Cinematic composition, dramatic lighting
- If showing a philosopher, describe them consistently across all slides

Example hook: "They gave Socrates a choice. Exile or death. He chose neither."

OUTPUT AS JSON:
{{
    "title": "Story title",
    "topic": "{topic}",
    "content_type": "narrative_story",
    "total_slides": 8,
    "slides": [
        {{
            "slide_number": 1,
            "slide_type": "hook",
            "title": "DRAMATIC HOOK",
            "content": "The hook...",
            "visual_description": "Opening cinematic shot - establish mood, setting, or character"
        }},
        {{
            "slide_number": 2,
            "slide_type": "setup",
            "title": "SCENE TITLE",
            "content": "Scene narration...",
            "visual_description": "Continuation of visual narrative - same style, progressing story"
        }},
        // ... more slides
    ]
}}
"""
}


# =============================================================================
# IMAGE GENERATION PROMPTS
# =============================================================================

def get_image_prompt(
    visual_description: str,
    image_style: str,
    slide_type: str = "content",
    content_type: str = None
) -> str:
    """
    Build the complete image generation prompt.

    Args:
        visual_description: The specific visual for this slide
        image_style: One of: classical, surreal, cinematic, minimal
        slide_type: hook, content, list_item, insight, outro
        content_type: Optional content type for additional context

    Returns:
        Complete prompt for image generation
    """
    style_config = IMAGE_STYLES.get(image_style, IMAGE_STYLES["classical"])

    # Select the appropriate style prompt based on slide type
    if slide_type == "hook":
        style_prompt = style_config.hook_prompt
    elif slide_type in ["outro", "cta"]:
        style_prompt = style_config.outro_prompt
    else:
        style_prompt = style_config.content_prompt

    # Build the complete prompt with visual description FIRST
    prompt = f"""PRIMARY SUBJECT (generate this exactly):
{visual_description}

{style_prompt}

TECHNICAL REQUIREMENTS:
- Do NOT include any text, words, letters, or numbers
- Leave center area relatively clean for text overlay
- Vertical 9:16 aspect ratio for mobile

AVOID: {style_config.negative_prompt}"""

    return prompt


def get_script_prompt(topic: str, content_type: str) -> str:
    """
    Get the script generation prompt for a content type.

    Args:
        topic: The topic to generate content about
        content_type: One of: list_educational, list_existential, wisdom_slideshow, narrative_story

    Returns:
        Complete prompt for script generation
    """
    template = SCRIPT_PROMPTS.get(content_type, SCRIPT_PROMPTS["wisdom_slideshow"])
    return template.format(topic=topic)


def get_content_type_config(content_type: str) -> ContentTypeConfig:
    """Get configuration for a content type."""
    return CONTENT_TYPES.get(content_type, CONTENT_TYPES["wisdom_slideshow"])


def get_image_style_config(image_style: str) -> ImageStyleConfig:
    """Get configuration for an image style."""
    return IMAGE_STYLES.get(image_style, IMAGE_STYLES["classical"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def list_content_types() -> List[Dict]:
    """List all content types for UI."""
    return [
        {
            "id": ct.id,
            "name": ct.name,
            "description": ct.description,
            "example": ct.example,
            "default_image_style": ct.default_image_style,
        }
        for ct in CONTENT_TYPES.values()
    ]


def list_image_styles() -> List[Dict]:
    """List all image styles for UI."""
    return [
        {
            "id": style.id,
            "name": style.name,
            "description": style.description,
        }
        for style in IMAGE_STYLES.values()
    ]
