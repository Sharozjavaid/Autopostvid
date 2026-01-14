#!/usr/bin/env python3
"""
Theme Configuration for Philosophy Video Generator

Central configuration for all content themes. Each theme defines:
- Content types it supports (list, narrative, single-topic)
- Script generation style/tone
- Image generation prompts (dialed-in)
- Text overlay settings (programmatic vs AI-burned)
- Font and color configurations

Themes sync script style with image style for consistent output.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ContentType(Enum):
    """Types of content a theme can produce"""
    LIST_SLIDESHOW = "list_slideshow"           # "5 Philosophers Who..."
    NARRATIVE_VIDEO = "narrative_video"          # Story retellings with voiceover
    SINGLE_TOPIC = "single_topic"               # Deep dive on one philosopher
    COMPARISON = "comparison"                    # Before/after, contrasts
    QUOTE_CARDS = "quote_cards"                 # Single quote visuals


class TextOverlayMode(Enum):
    """How text is added to images"""
    PROGRAMMATIC = "programmatic"    # Pillow adds text after (consistent, cheap)
    AI_BURNED = "ai_burned"          # AI generates text in image (stylized, expensive)
    HYBRID = "hybrid"                # AI background + programmatic text


@dataclass
class TextConfig:
    """Text overlay configuration"""
    mode: TextOverlayMode = TextOverlayMode.PROGRAMMATIC
    font_name: str = "montserrat"           # montserrat, bebas, cinzel, oswald, cormorant
    title_color: str = "#FFFFFF"            # White default
    subtitle_color: str = "#CCCCCC"         # Light gray
    number_color: str = "#FFFFFF"           # For "#1", "#2" etc.
    shadow_enabled: bool = True
    shadow_color: str = "#000000"
    outline_enabled: bool = False
    outline_color: str = "#000000"
    # AI-burned text style (when mode is AI_BURNED)
    ai_text_style: str = "bold golden metallic 3D text with emboss effect"


@dataclass
class ScriptConfig:
    """Script generation configuration"""
    tone: str = "dramatic"                  # dramatic, educational, confrontational, storytelling
    hook_style: str = "bold_statement"      # bold_statement, question, controversial, mystery
    word_count_per_scene: int = 12          # Target words per scene
    total_scenes: int = 7                   # Hook + content + outro
    include_cta: bool = True                # Call to action in outro
    # Script structure hints
    structure_notes: str = ""


@dataclass
class ImageConfig:
    """Image generation configuration"""
    model: str = "gpt15"                    # gpt15, flux, dalle3
    base_prompt: str = ""                   # Core visual style prompt
    hook_prompt: str = ""                   # Specific prompt for hook/intro slides
    content_prompt: str = ""                # Specific prompt for content slides
    outro_prompt: str = ""                  # Specific prompt for outro slides
    # Composition hints
    leave_center_clear: bool = True         # For programmatic text overlay
    aspect_ratio: str = "9:16"
    negative_prompt: str = "text, words, letters, watermark, signature, blurry, low quality"


@dataclass
class Theme:
    """Complete theme configuration"""
    id: str
    name: str
    description: str
    content_types: List[ContentType]
    script_config: ScriptConfig
    image_config: ImageConfig
    text_config: TextConfig
    # Example topics for this theme
    example_topics: List[str] = field(default_factory=list)
    # Whether this theme is active
    enabled: bool = True


# =============================================================================
# THEME DEFINITIONS
# =============================================================================

THEMES: Dict[str, Theme] = {

    # =========================================================================
    # THEME 1: GLITCH TITANS
    # For: List hooks/intros with dramatic impact
    # Visual: Cracked glass, digital glitch artifacts, row of philosopher faces
    # Text: Gold 3D metallic (AI-burned) OR white programmatic
    # =========================================================================
    "glitch_titans": Theme(
        id="glitch_titans",
        name="Glitch Titans",
        description="Dramatic list intros with cracked glass overlay, digital glitch effects, and row of philosopher busts. Perfect for '5 Philosophers Who Changed Everything' style hooks.",
        content_types=[ContentType.LIST_SLIDESHOW],
        script_config=ScriptConfig(
            tone="dramatic",
            hook_style="bold_statement",
            word_count_per_scene=10,
            total_scenes=7,
            include_cta=True,
            structure_notes="""
            - Hook: Ultra short, punchy statement (THEY CHANGED EVERYTHING)
            - Each item: Name + single powerful idea
            - Outro: Challenge or call to action
            - Use uppercase for impact
            """
        ),
        image_config=ImageConfig(
            model="gpt15",
            base_prompt="""Dark moody digital artwork with cracked glass overlay effect.
Shattered screen aesthetic with white fracture lines spreading across the image.
Digital glitch artifacts - RGB color separation, pixel distortion, scan lines.
Deep black background with subtle blue/cyan digital noise.
Cyberpunk meets classical aesthetic.
Vertical 9:16 aspect ratio for TikTok/mobile.
High contrast, dramatic lighting from behind.""",

            hook_prompt="""Dark digital artwork with dramatic cracked glass overlay effect.
COMPOSITION: Row of 4-5 classical marble philosopher busts/portraits at the bottom third.
Mix of ancient (Socrates, Plato, Marcus Aurelius) and modern thinkers (Nietzsche, Descartes).
Busts should be grayscale/monochrome with slight blue tint.
EFFECTS: White cracked glass fractures spreading from corners across the image.
Subtle RGB glitch distortion on the edges of the busts.
Horizontal scan lines and digital noise artifacts.
BACKGROUND: Pure black with faint blue digital matrix pattern.
LIGHTING: Dramatic backlighting creating silhouette edges on busts.
STYLE: Cyberpunk meets ancient wisdom aesthetic.
NO TEXT - leave upper 2/3 of image clear for text overlay.
Vertical 9:16 mobile format.""",

            content_prompt="""Dark atmospheric portrait of [PHILOSOPHER_NAME] as a classical marble bust.
STYLE: Grayscale with subtle blue/cyan digital tint.
Digital glitch effects - RGB separation on edges, scan lines.
Cracked glass overlay with white fracture lines.
BACKGROUND: Deep black with faint digital noise pattern.
COMPOSITION: Bust centered, dramatic side lighting.
Leave center-bottom area clear for text overlay.
Vertical 9:16 format.""",

            outro_prompt="""Dark digital artwork with multiple marble philosopher busts arranged in a group.
Cracked glass overlay with white fractures.
Digital glitch effects - RGB separation, scan lines.
Dramatic backlighting creating glowing edges.
Deep black background with blue digital noise.
Composition suggests 'choose your path' - busts looking different directions.
Leave center clear for call-to-action text.
Vertical 9:16 format.""",

            leave_center_clear=True,
            negative_prompt="text, words, letters, numbers, watermark, bright colors, daylight, modern clothing"
        ),
        text_config=TextConfig(
            mode=TextOverlayMode.PROGRAMMATIC,  # Can switch to AI_BURNED
            font_name="bebas",                   # Bold, impactful
            title_color="#FFD700",               # Gold for titles
            subtitle_color="#FFFFFF",            # White for subtitles
            number_color="#FFD700",              # Gold for numbers
            shadow_enabled=True,
            shadow_color="#000000",
            ai_text_style="bold golden yellow 3D metallic text with emboss effect, dramatic cinematic typography, slight glow"
        ),
        example_topics=[
            "5 Philosophers Who Changed Everything",
            "7 Ancient Thinkers Who Predicted the Future",
            "The 5 Men Who Secretly Designed the Modern World",
            "4 Philosophers Every Entrepreneur Must Study",
            "6 Minds That Destroyed Reality"
        ],
        enabled=True
    ),

    # =========================================================================
    # THEME 2: OIL CONTRAST
    # For: Narrative/transformation stories, before/after comparisons
    # Visual: Split-scene oil painting, modern vs ancient, rich Baroque style
    # Text: Gold serif (AI-burned works well here)
    # =========================================================================
    "oil_contrast": Theme(
        id="oil_contrast",
        name="Oil Contrast",
        description="Split-scene oil paintings showing transformation/contrast. Perfect for 'True Happiness' style narratives comparing modern struggle vs ancient wisdom.",
        content_types=[ContentType.NARRATIVE_VIDEO, ContentType.COMPARISON],
        script_config=ScriptConfig(
            tone="storytelling",
            hook_style="contrast",
            word_count_per_scene=15,
            total_scenes=8,
            include_cta=True,
            structure_notes="""
            - Hook: Present the contrast/conflict
            - Build: Show the 'before' state (modern struggle)
            - Turn: Introduce ancient wisdom
            - Payoff: Show transformation
            - Outro: Invite viewer to choose
            - Narrative arc with emotional journey
            """
        ),
        image_config=ImageConfig(
            model="gpt15",
            base_prompt="""Renaissance oil painting style in the manner of Caravaggio and Rembrandt.
Rich warm color palette - deep burgundy, golden amber, burnt sienna, dark umber.
Dramatic chiaroscuro lighting with strong shadows and golden highlights.
Visible brushstroke texture suggesting classical oil on canvas.
Baroque theatrical drama and emotional intensity.
Vertical 9:16 aspect ratio.""",

            hook_prompt="""Split-scene Renaissance oil painting, vertical composition divided in half.
LEFT SIDE: Modern man in despair - hunched over table with junk food, gaming controller, phone.
Dim bluish light from screens, dark shadows, defeated posture.
Contemporary clothing but painted in classical oil style.
RIGHT SIDE: Same man transformed - heroic pose, ancient Roman/Greek attire.
Warm golden light, confident upward gaze, muscular and proud.
Classical sculpture or bust visible in background.
STYLE: Caravaggio chiaroscuro lighting, rich warm oils.
Clear vertical divide between the two halves.
Leave center horizontal band clear for text overlay.
Vertical 9:16 format.""",

            content_prompt="""Renaissance oil painting of [PHILOSOPHER_NAME] in classical setting.
[SCENE_DESCRIPTION]
Caravaggio-style dramatic lighting - single light source creating deep shadows.
Rich color palette: burgundy drapes, golden highlights, deep brown shadows.
Classical setting - Roman/Greek architecture, columns, marble floors.
[PHILOSOPHER_DESCRIPTION] with emotional intensity in facial expression and body language.
Oil on canvas texture with visible brushstrokes.
Leave lower third clear for text overlay.
Vertical 9:16 format.""",

            outro_prompt="""Renaissance oil painting showing a figure at a crossroads.
Two paths visible - one leading to modern chaos (screens, clutter),
one leading to classical wisdom (temple, scrolls, light).
Dramatic Caravaggio lighting illuminating the choice.
Figure shown from behind, contemplating the decision.
Rich warm oil painting colors - gold, burgundy, amber.
Leave center clear for call-to-action text.
Vertical 9:16 format.""",

            leave_center_clear=True,
            negative_prompt="text, words, cartoon, anime, 3D render, modern photography, bright flat lighting"
        ),
        text_config=TextConfig(
            mode=TextOverlayMode.PROGRAMMATIC,
            font_name="cinzel",                  # Classical serif
            title_color="#FFD700",               # Gold
            subtitle_color="#F5E6D3",            # Warm cream
            shadow_enabled=True,
            shadow_color="#2D1810",              # Dark brown shadow
            ai_text_style="elegant golden serif text with Renaissance styling, slight 3D depth, warm glow"
        ),
        example_topics=[
            "True Happiness: What the Ancients Knew",
            "The Transformation of Marcus Aurelius",
            "From Slave to Sage: The Epictetus Story",
            "Modern Anxiety vs Ancient Peace",
            "The Death of Socrates: A Story of Courage"
        ],
        enabled=True
    ),

    # =========================================================================
    # THEME 3: GOLDEN DUST
    # For: Clean list slideshows with elegant presentation
    # Visual: Sepia/gold marble busts, atmospheric dust particles, warm glow
    # Text: White sans-serif (programmatic) - clean and readable
    # =========================================================================
    "golden_dust": Theme(
        id="golden_dust",
        name="Golden Dust",
        description="Elegant sepia-toned marble busts with golden atmospheric particles. Perfect for clean, educational list slideshows with white text overlay.",
        content_types=[ContentType.LIST_SLIDESHOW, ContentType.SINGLE_TOPIC],
        script_config=ScriptConfig(
            tone="educational",
            hook_style="mystery",
            word_count_per_scene=12,
            total_scenes=7,
            include_cta=True,
            structure_notes="""
            - Hook: Intriguing statement that creates curiosity
            - Each item: Name + key contribution/idea + why it matters
            - More informative than dramatic
            - Outro: Summary and invitation to learn more
            """
        ),
        image_config=ImageConfig(
            model="gpt15",
            base_prompt="""Sepia-toned classical artwork with golden atmospheric lighting.
Marble busts and sculptures with warm amber/gold color grading.
Floating dust particles catching golden light.
Ethereal, museum-quality presentation.
Rich golden-brown color palette - sepia, amber, bronze, cream.
Soft bokeh background with warm glow.
Vertical 9:16 aspect ratio.""",

            hook_prompt="""Group of 4-5 classical marble philosopher busts arranged in dramatic formation.
STYLE: Sepia/golden monochrome color grading - warm amber tones throughout.
Busts are detailed Greek/Roman style - Socrates, Plato, Aristotle, etc.
ATMOSPHERE: Golden dust particles floating in the air, catching light.
Ethereal golden glow emanating from behind the busts.
BACKGROUND: Soft gradient from dark brown to golden amber.
Bokeh light spots creating depth.
COMPOSITION: Busts arranged with central figure prominent, others flanking.
Leave middle section clear for text overlay.
Vertical 9:16 mobile format.""",

            content_prompt="""Single classical marble bust of [PHILOSOPHER_NAME].
STYLE: Sepia/golden monochrome - warm amber and bronze tones.
Detailed Greek/Roman sculptural style with realistic features.
ATMOSPHERE: Golden dust particles floating around the bust.
Soft golden glow from behind creating rim lighting.
BACKGROUND: Gradient from dark sepia to warm golden amber.
Soft bokeh light particles.
COMPOSITION: Bust in upper portion, leave lower half clear for text.
Vertical 9:16 format.""",

            outro_prompt="""Collection of marble philosopher busts fading into golden light.
Sepia/amber color grading throughout.
Dense golden dust particles creating ethereal atmosphere.
Busts arranged at various depths, some sharp, some soft/faded.
Warm glowing light source from center/behind.
Suggests infinite wisdom extending beyond the frame.
Leave center clear for call-to-action text.
Vertical 9:16 format.""",

            leave_center_clear=True,
            negative_prompt="text, words, color, blue, green, red, modern elements, bright white"
        ),
        text_config=TextConfig(
            mode=TextOverlayMode.PROGRAMMATIC,
            font_name="montserrat",              # Clean sans-serif
            title_color="#FFFFFF",               # Pure white
            subtitle_color="#E8E8E8",            # Soft white
            number_color="#FFFFFF",
            shadow_enabled=True,
            shadow_color="#1A1408",              # Dark sepia shadow
            outline_enabled=False
        ),
        example_topics=[
            "The 5 Men Who Secretly Designed the Modern World",
            "7 Stoic Quotes That Will Change Your Life",
            "5 Philosophers Every Student Should Know",
            "Ancient Wisdom for Modern Problems",
            "The Greatest Minds in History"
        ],
        enabled=True
    ),

    # =========================================================================
    # THEME 4: SCENE PORTRAIT
    # For: Individual slides with full scenes, single-topic deep dives
    # Visual: Philosopher in their setting (temple, library, prison, etc.)
    # Text: White programmatic with number, name, subtitle format
    # =========================================================================
    "scene_portrait": Theme(
        id="scene_portrait",
        name="Scene Portrait",
        description="Full cinematic scenes with individual philosophers in their historical setting. Perfect for detailed bios, quotes, and single-topic slideshows.",
        content_types=[ContentType.LIST_SLIDESHOW, ContentType.SINGLE_TOPIC, ContentType.QUOTE_CARDS],
        script_config=ScriptConfig(
            tone="biographical",
            hook_style="bold_statement",
            word_count_per_scene=15,
            total_scenes=7,
            include_cta=True,
            structure_notes="""
            - Hook: Powerful statement about the philosopher or topic
            - Each slide: #Number, NAME, brief powerful description
            - Include context (born a slave, emperor, etc.)
            - Quote or key teaching
            - Outro: Challenge viewer to apply the wisdom
            """
        ),
        image_config=ImageConfig(
            model="gpt15",
            base_prompt="""Cinematic photorealistic scene of ancient philosopher in historical setting.
Dramatic Caravaggio-style lighting with warm fire/candlelight.
Rich detailed environment - temple columns, stone steps, fire bowls, scrolls.
Atmospheric haze and dust particles visible in light beams.
Film-quality composition and color grading.
Warm color palette - amber, gold, burgundy, stone gray.
Vertical 9:16 aspect ratio optimized for mobile.""",

            hook_prompt="""Cinematic scene of ancient temple or agora at golden hour.
Multiple philosophers gathered in discussion or contemplation.
Dramatic columns, stone architecture, fire bowls with flames.
Warm golden light streaming through, dust particles visible.
Atmospheric and mysterious mood.
No single figure dominant - suggests a gathering of wisdom.
Leave center area clear for hook text.
Vertical 9:16 format.""",

            content_prompt="""Cinematic portrait of [PHILOSOPHER_NAME] in [SETTING].
FIGURE: [PHILOSOPHER_DESCRIPTION] - aged wise man with beard, wearing [CLOTHING].
Seated/standing in [POSE] showing [EMOTION/QUALITY].
SETTING: [ENVIRONMENT_DETAILS] - temple steps, fire bowls, columns, chains, scrolls.
LIGHTING: Dramatic Caravaggio-style, warm firelight from [DIRECTION].
Atmospheric haze, dust particles visible in light beams.
MOOD: [EMOTIONAL_TONE] - contemplative, defiant, peaceful, wise.
COMPOSITION: Figure in upper 2/3, leave lower third clear for text.
Vertical 9:16 format.""",

            outro_prompt="""Cinematic scene of empty philosopher's seat or path.
Ancient setting - temple, library, or garden.
Warm golden light suggesting dawn or invitation.
The seat/path is open, inviting the viewer to take their place.
Scrolls, books, or symbols of wisdom nearby.
Atmospheric and aspirational mood.
Leave center clear for call-to-action text.
Vertical 9:16 format.""",

            leave_center_clear=True,
            negative_prompt="text, words, modern elements, cartoon, anime, bright flat lighting, stock photo look"
        ),
        text_config=TextConfig(
            mode=TextOverlayMode.PROGRAMMATIC,
            font_name="montserrat",              # Clean, readable
            title_color="#FFFFFF",               # White name
            subtitle_color="#E0E0E0",            # Light gray description
            number_color="#FFFFFF",              # White number
            shadow_enabled=True,
            shadow_color="#000000",
            outline_enabled=False
        ),
        example_topics=[
            "5 Stoic Philosophers Every Man Should Know",
            "Marcus Aurelius: The Philosopher Emperor",
            "The Life of Epictetus: From Slave to Sage",
            "Seneca's Greatest Teachings",
            "Lao Tzu and the Way"
        ],
        enabled=True
    ),
}


# =============================================================================
# PHILOSOPHER DATABASE (for scene_portrait theme)
# =============================================================================

PHILOSOPHER_SCENES = {
    "socrates": {
        "name": "Socrates",
        "description": "elderly Greek man with balding head, snub nose, thick beard, piercing eyes",
        "clothing": "simple white chiton (Greek robe), barefoot",
        "settings": [
            "Athenian agora with marble columns and citizens",
            "prison cell before his execution, holding cup",
            "outdoor gathering with young students around him"
        ],
        "poses": ["seated in discussion", "standing questioning", "drinking hemlock calmly"],
        "mood": "questioning, ironic wisdom, peaceful acceptance"
    },
    "plato": {
        "name": "Plato",
        "description": "broad-shouldered man with full beard, noble bearing, thoughtful expression",
        "clothing": "elegant draped toga, sandals",
        "settings": [
            "the Academy with gardens and colonnades",
            "cave entrance with shadows on walls",
            "writing at desk with scrolls"
        ],
        "poses": ["gesturing upward toward ideals", "writing", "teaching students"],
        "mood": "visionary, intellectual, contemplative"
    },
    "aristotle": {
        "name": "Aristotle",
        "description": "well-groomed man with trimmed beard, intelligent eyes, scholarly demeanor",
        "clothing": "refined Greek robes, holding scroll or book",
        "settings": [
            "Lyceum with walking paths (peripatetic)",
            "study filled with specimens and scrolls",
            "teaching Alexander the Great as a youth"
        ],
        "poses": ["walking while teaching", "examining specimen", "reading scroll"],
        "mood": "analytical, curious, systematic"
    },
    "marcus_aurelius": {
        "name": "Marcus Aurelius",
        "description": "Roman emperor with curly hair and beard, tired but noble eyes, weathered face",
        "clothing": "imperial purple toga or military armor",
        "settings": [
            "military tent on frontier, writing by candlelight",
            "Roman throne room with marble columns",
            "battlefield at dawn, contemplating"
        ],
        "poses": ["writing in journal", "standing in armor gazing at horizon", "seated in meditation"],
        "mood": "stoic resolve, weary wisdom, duty-bound"
    },
    "epictetus": {
        "name": "Epictetus",
        "description": "older man with long white beard, weathered face, lame leg, eyes full of hard-won wisdom",
        "clothing": "simple worn tunic, sitting on stone",
        "settings": [
            "humble room with single lamp, teaching students",
            "temple steps with broken chains nearby",
            "simple garden, speaking to followers"
        ],
        "poses": ["seated on stone steps teaching", "gesturing emphatically", "peaceful meditation"],
        "mood": "resilient, passionate teaching, inner freedom"
    },
    "seneca": {
        "name": "Seneca",
        "description": "Roman man with receding hairline, sharp features, wealthy but troubled appearance",
        "clothing": "fine Roman toga, rings and jewelry",
        "settings": [
            "luxurious villa with contradictory simplicity",
            "writing letters by lamplight",
            "facing Nero's soldiers with dignity"
        ],
        "poses": ["writing at ornate desk", "standing defiantly", "in bath (final moments)"],
        "mood": "conflicted wisdom, eloquent, facing mortality"
    },
    "diogenes": {
        "name": "Diogenes",
        "description": "unkempt man with wild beard, muscular from simple living, mischievous eyes",
        "clothing": "ragged cloak only, barefoot, carrying lantern",
        "settings": [
            "living in large ceramic jar/barrel in marketplace",
            "confronting Alexander the Great",
            "walking through Athens with lantern in daylight"
        ],
        "poses": ["lounging in barrel", "holding lantern searching", "mocking the wealthy"],
        "mood": "irreverent, provocative, radically free"
    },
    "confucius": {
        "name": "Confucius",
        "description": "dignified Chinese elder with long beard, traditional topknot, kind but serious eyes",
        "clothing": "flowing Han dynasty robes, scholarly cap",
        "settings": [
            "teaching disciples in garden pavilion",
            "traveling on dusty road between kingdoms",
            "ancestral temple with incense"
        ],
        "poses": ["seated teaching", "bowing respectfully", "contemplating ancient texts"],
        "mood": "dignified wisdom, social harmony, respectful"
    },
    "lao_tzu": {
        "name": "Lao Tzu",
        "description": "ancient Chinese sage with very long white beard, peaceful ethereal expression",
        "clothing": "simple Taoist robes, riding water buffalo",
        "settings": [
            "mountain pass, departing civilization",
            "misty bamboo forest in meditation",
            "writing the Tao Te Ching at border gate"
        ],
        "poses": ["riding ox westward", "meditating in nature", "writing with brush"],
        "mood": "mysterious, flowing like water, detached serenity"
    },
    "nietzsche": {
        "name": "Friedrich Nietzsche",
        "description": "German man with enormous walrus mustache, intense eyes, serious expression",
        "clothing": "19th century suit and coat, sometimes disheveled",
        "settings": [
            "alpine mountain overlook in Switzerland",
            "dark study surrounded by books",
            "walking alone on dramatic cliffside"
        ],
        "poses": ["staring intensely forward", "writing feverishly", "silhouetted against sky"],
        "mood": "intense, prophetic, tragically brilliant"
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_theme(theme_id: str) -> Optional[Theme]:
    """Get a theme by ID"""
    return THEMES.get(theme_id)


def get_enabled_themes() -> Dict[str, Theme]:
    """Get all enabled themes"""
    return {k: v for k, v in THEMES.items() if v.enabled}


def get_themes_for_content_type(content_type: ContentType) -> List[Theme]:
    """Get all themes that support a given content type"""
    return [t for t in THEMES.values() if content_type in t.content_types and t.enabled]


def get_philosopher_scene(philosopher_key: str) -> Optional[dict]:
    """Get scene data for a specific philosopher"""
    return PHILOSOPHER_SCENES.get(philosopher_key.lower().replace(" ", "_"))


def build_scene_prompt(theme: Theme, philosopher_key: str, scene_index: int = 0) -> str:
    """Build a complete image prompt for a philosopher scene"""
    philosopher = get_philosopher_scene(philosopher_key)
    if not philosopher:
        return theme.image_config.content_prompt

    prompt = theme.image_config.content_prompt

    # Replace placeholders
    replacements = {
        "[PHILOSOPHER_NAME]": philosopher["name"],
        "[PHILOSOPHER_DESCRIPTION]": philosopher["description"],
        "[CLOTHING]": philosopher["clothing"],
        "[SETTING]": philosopher["settings"][scene_index % len(philosopher["settings"])],
        "[ENVIRONMENT_DETAILS]": philosopher["settings"][scene_index % len(philosopher["settings"])],
        "[POSE]": philosopher["poses"][scene_index % len(philosopher["poses"])],
        "[EMOTION/QUALITY]": philosopher["mood"],
        "[EMOTIONAL_TONE]": philosopher["mood"],
        "[DIRECTION]": "the side"
    }

    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt


def list_all_themes() -> None:
    """Print summary of all themes"""
    print("\n" + "="*60)
    print("AVAILABLE THEMES")
    print("="*60)

    for theme_id, theme in THEMES.items():
        status = "ENABLED" if theme.enabled else "DISABLED"
        print(f"\n[{status}] {theme.name} ({theme_id})")
        print(f"  {theme.description[:80]}...")
        print(f"  Content types: {[ct.value for ct in theme.content_types]}")
        print(f"  Text mode: {theme.text_config.mode.value}")
        print(f"  Font: {theme.text_config.font_name}")
        print(f"  Examples: {theme.example_topics[:2]}")


# =============================================================================
# MAIN - Preview themes
# =============================================================================

if __name__ == "__main__":
    list_all_themes()

    print("\n" + "="*60)
    print("EXAMPLE: Building scene prompt for Epictetus")
    print("="*60)

    theme = get_theme("scene_portrait")
    if theme:
        prompt = build_scene_prompt(theme, "epictetus", 0)
        print(f"\nGenerated prompt:\n{prompt}")
