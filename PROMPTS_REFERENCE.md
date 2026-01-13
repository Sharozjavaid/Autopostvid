# AI Model Prompts Reference Sheet

This document aggregates all unique prompts used for AI models (text generation and image generation) across the philosophy video generator codebase.

---

## 📋 Overview

| Category | File | Model/API | Purpose |
|----------|------|-----------|---------|
| **Text Generation** | `gemini_handler.py` | Gemini 3 Pro Preview | Script generation (narrative + list) |
| **Text Generation** | `gemini_handler.py` | Gemini 3 Pro Preview | Slideshow script generation |
| **Text Generation** | `gemini_handler.py` | Gemini 2.0 Flash Exp | Scene analysis for image prompts |
| **Text Generation** | `caption_generator.py` | GPT-5 Nano | TikTok caption generation |
| **Image Generation** | `image_generator.py` | Gemini 3 Pro Image Preview | Basic philosophy images (deprecated) |
| **Image Generation** | `smart_image_generator.py` | Gemini 3 Pro Image Preview | Smart images with text overlays |
| **Image Generation** | `openai_image_generator.py` | DALL-E 3 / GPT Image 1.5 | Philosophy scene images |
| **Image Generation** | `gpt_image_generator.py` | GPT Image 1.5 via fal.ai | Bold text overlay images |
| **Image Generation** | `slideshow_generator.py` | GPT Image 1.5 via fal.ai | TikTok slideshow slides |
| **Image Generation** | `tiktok_slideshow.py` | Flux Schnell / DALL-E 3 via fal.ai | Background images only |
| **Video Generation** | `fal_video_generator.py` | MiniMax Hailuo-02 via fal.ai | Image-to-video transitions |

---

## 🎭 TEXT GENERATION PROMPTS

### 1. List-Style Content Script (`gemini_handler.py`)

**Model:** `gemini-3-pro-preview`  
**Used by:** `_generate_list_content()`  
**Purpose:** Generate viral list-style video scripts (e.g., "5 philosophers who...")

```
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
{
    "script": "full narration text - the complete voiceover script",
    "scenes": [
        {
            "scene_number": 1,
            "text": "portion of script for this scene - EXACTLY 12-15 WORDS",
            "word_count": 14,
            "target_duration": 6,
            "visual_description": "vivid, specific image description",
            "slide_subject": "BOLD TEXT OVERLAY - e.g., '#1 SOCRATES' or 'THE TRUTH'",
            "list_item": 0,
            "key_concept": "main idea for this scene"
        }
    ],
    "hook": "the attention-grabbing opening line",
    "list_items": [
        {
            "number": 1,
            "name": "Name of philosopher/concept",
            "quote_or_idea": "The main quote or key idea",
            "explanation": "Why this matters - make it personal and impactful"
        }
    ],
    "total_word_count": {total_words},
    "estimated_duration_seconds": {num_scenes * 6}
}
```

**Key Differences from Narrative:**
- Focus on individual list items vs. continuous story arc
- Includes `list_item` field for tracking position
- More emphasis on "ranking" format (#1, #2, etc.)
- Each item is self-contained

---

### 2. Narrative Story Script (`gemini_handler.py`)

**Model:** `gemini-3-pro-preview`  
**Used by:** `_generate_narrative_story()`  
**Purpose:** Generate engaging story-based scripts (e.g., "Plato's Cave Allegory")

```
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
```

**Key Differences from List:**
- Continuous narrative arc vs. individual items
- Includes `climax_scenes` field to identify peak moments
- More focus on tension building and payoff
- Scene-to-scene flow is critical

---

### 3. Slideshow Script (`gemini_handler.py`)

**Model:** `gemini-3-pro-preview`  
**Used by:** `generate_slideshow_script()`  
**Purpose:** Generate TikTok slideshow content (static images with text)

```
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

📖 CONTENT SLIDES (slides 1-N):
Each slide after the hook is ONE piece of content (one lesson, one reason, one person).

Even when talking about modern people, connect their success to philosophical principles:
- Steve Jobs → Connect to Zen Buddhism, simplicity philosophy, "focus" wisdom
- Elon Musk → Connect to first principles thinking (Aristotle), Stoic persistence
- Oprah → Connect to Stoic resilience, growth mindset philosophy

🔥 SUBTITLE FORMULAS (for content slides):

❌ BAD: "Steve Jobs valued simplicity."
✅ GOOD: "He followed one Zen principle: 'Simplicity is the ultimate sophistication.'"

❌ BAD: "Marcus Aurelius practiced controlling his emotions."
✅ GOOD: "He ruled Rome. Every night he asked: 'Was I good today?' CEOs still do this."

🎨 VISUAL DESCRIPTION RULES (CRITICAL):

The background image MUST visually represent WHAT THE SLIDE IS ABOUT.

✅ GOOD EXAMPLES:

Slide about STEVE JOBS:
- display_text: "STEVE JOBS"
- subtitle: "He started in a garage. His rule? 'Don't waste time living someone else's life.'"
- visual_description: "Steve Jobs silhouette in black turtleneck, minimalist white/gray background, holding glowing Apple logo or lightbulb, clean iconic aesthetic"

Slide about MARCUS AURELIUS:
- display_text: "MARCUS AURELIUS"  
- subtitle: "He ruled Rome. Every night he asked: 'Was I good today?'"
- visual_description: "Roman emperor in purple robes writing in journal by candlelight, marble columns, warm golden lighting, classical oil painting style"

REQUIREMENTS:
- display_text: 2-6 words max (ALL CAPS)
- subtitle: 8-15 words (punchy, memorable, emotional)
- visual_description: MUST match the slide subject
- Total slides: 5-7
```

**Key Differences from Script Generation:**
- Optimized for static images (slideshow format)
- Shorter text (display_text is 2-6 words)
- Visual description must match slide subject literally
- Philosophy connection is MANDATORY in every hook

---

### 4. Scene Analysis for Image Prompts (`smart_image_generator.py`)

**Model:** `gemini-2.0-flash-exp`  
**Used by:** `analyze_story_and_generate_image_prompts()`  
**Purpose:** Create intelligent image prompts from story scenes

```
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
{
    "story_analysis": "Brief description of the overall visual narrative",
    "overall_aesthetic": "The unifying visual style for all scenes",
    "scene_prompts": [
        {
            "scene_number": 1,
            "philosophical_concept": "The key idea being visualized",
            "mood": "The emotional tone",
            "image_prompt": "Detailed prompt for image generation - include lighting, composition, style, colors"
        }
    ]
}
```

---

### 5. TikTok Caption Generation (`caption_generator.py`)

**Model:** `gpt-5-nano`  
**Used by:** `generate_caption()`  
**Purpose:** Generate TikTok captions with hashtags

**System Message:**
```
You are a social media expert who creates viral TikTok captions for philosophy content.
```

**User Prompt:**
```
Generate a short, engaging TikTok caption for a philosophy video about: {context}

Requirements:
- Keep it under 150 characters (excluding hashtags)
- Make it thought-provoking and scroll-stopping
- Use a conversational, engaging tone
- Add 5-7 relevant hashtags at the end
- MUST include #PhilosophizeMeApp as one of the hashtags
- Other hashtags should be relevant to philosophy, the specific topic, and TikTok trends

Example format:
"This changed how I see everything... 🤯 #PhilosophizeMeApp #philosophy #wisdom #mindset #fyp #deep"

Generate only the caption text, nothing else.
```

**Key Difference:**
- Uses OpenAI GPT-5 Nano (not Gemini)
- Has system message + user prompt format
- Very short output (caption only)
- Must include branded hashtag

---

## 🖼️ IMAGE GENERATION PROMPTS

### 6. Basic Philosophy Image (`image_generator.py`)

**Model:** `gemini-3-pro-image-preview`  
**Used by:** `generate_philosophy_image()`  
**Purpose:** Generate classical philosophy images (legacy, mostly deprecated)

```
Create a stunning philosophical image in classical painting style.

Story: {story_title}
Scene Context: {scene_text}
Visual Description: {visual_desc}
Key Concept: {key_concept}

Style Requirements:
- Classical Renaissance/Baroque painting aesthetic
- Dark, moody atmosphere with dramatic chiaroscuro lighting
- Rich, deep colors: golds, deep blues, burgundy, dark browns
- Mysterious shadows with strategic golden highlights
- Philosophical symbolism and metaphorical elements
- Vertical composition optimized for 9:16 TikTok format
- Contemplative, introspective mood
- Ancient or timeless setting elements

Visual Elements to Include:
- Dramatic lighting that creates depth and mystery
- Classical architectural elements if relevant
- Symbolic objects (scrolls, books, candles, mirrors)
- Figures in contemplative poses
- Atmospheric effects (mist, soft glows, shadows)

The image should evoke wonder, introspection, and the pursuit of wisdom.
Make it visually striking enough to stop scrollers on TikTok.
```

---

### 7. Smart Image with Text Overlay (`smart_image_generator.py`)

**Model:** `gemini-3-pro-image-preview`  
**Used by:** `generate_image_with_nano()`  
**Purpose:** Generate images with themed text burned in

**Text Overlay Instruction (prepended to prompt):**
```
CRITICAL TEXT REQUIREMENT: The image MUST prominently display the text "{text_overlay}" 
as large, bold, golden/yellow metallic lettering with a subtle 3D emboss effect.
The text should be centered in the frame, highly legible, with dramatic cinematic typography 
like a movie poster title. Use high contrast against the dark background.
The text style should match Renaissance/Baroque aesthetics with ornate, classical font styling.

Scene visual: {base_prompt}
```

**Additional suffix (if no aspect ratio specified):**
```
, 9:16 vertical aspect ratio, mobile wallpaper style
```

---

### 8. OpenAI Philosophy Image (`openai_image_generator.py`)

**Model:** `dall-e-3` or `gpt-image-1.5`  
**Used by:** `generate_philosophy_image()`  
**Purpose:** Generate philosophy images via OpenAI

```
A haunting classical painting in the style of Caravaggio or Rembrandt.

Story: {story_title}
Scene Context: {scene_text}
Visual Description: {visual_desc}
Key Concept: {key_concept}

Style Requirements:
- Classical Renaissance/Baroque painting aesthetic
- Dark, moody atmosphere with dramatic chiaroscuro lighting
- Rich, deep colors: golds, deep blues, burgundy, dark browns
- Mysterious shadows with strategic golden highlights
- Philosophical symbolism and metaphorical elements
- Vertical composition optimized for 9:16 TikTok format
- Contemplative, introspective mood
- Ancient or timeless setting elements

The image should evoke wonder, introspection, and the pursuit of wisdom.
Make it visually striking enough to stop scrollers on TikTok.
```

**Key Difference from Gemini:**
- Explicitly mentions "Caravaggio or Rembrandt" style
- Otherwise very similar to basic image prompt

---

### 9. GPT Image 1.5 with Bold Text (`gpt_image_generator.py`)

**Model:** `fal-ai/gpt-image-1.5`  
**Used by:** `generate_philosophy_image()`  
**Purpose:** Generate images with bold text overlay for video scenes (RECOMMENDED)

**Style Template:**
```
Dark moody classical oil painting style, dramatic Caravaggio chiaroscuro lighting, 
Renaissance/Baroque aesthetic, rich deep colors (burgundy, gold, deep blue), 
mysterious shadows with golden highlights, philosophical atmosphere.
{visual_description}
Bold text overlay prominently displaying: "{slide_subject}"
The text should be large, centered, golden/yellow metallic with slight 3D emboss effect,
cinematic movie poster typography style, highly legible against the dark background.
Vertical 9:16 aspect ratio, mobile format.
```

**Key Differences:**
- Uses fal.ai API (not direct OpenAI)
- Explicit "Bold text overlay prominently displaying" instruction
- More concise template format
- Consistent golden text styling

---

### 10. TikTok Slideshow Slides (`slideshow_generator.py`)

**Model:** `fal-ai/gpt-image-1.5`  
**Used by:** `generate_slide()` / `_build_slide_prompt()`  
**Purpose:** Generate TikTok-style slideshow images with text

**Text Styling Instruction (used in all slide types):**
```
TEXT STYLING (CRITICAL - THIS IS THE MOST IMPORTANT PART):
- Text must be PERFECTLY CRISP and READABLE - this is a slideshow, text is everything
- Use clean, modern sans-serif font (like the fonts in TikTok/CapCut: bold, simple)
- WHITE text with a subtle black shadow/outline for maximum readability
- Text should be CENTERED and PROMINENT
- NO decorative/fancy fonts - just clean, bold, modern typography
- The text should look like it was added in a video editor (CapCut style)
- Text should pop against the background
```

**Hook Slide Prompt:**
```
Create a viral TikTok slideshow HOOK image. This is the first slide that needs to grab attention.

BACKGROUND:
{visual_description if visual_description else "Dark, moody, cinematic background. Could be abstract dark gradients, silhouettes, or atmospheric imagery. The background should NOT compete with the text."}

{tiktok_text_style}

TEXT TO DISPLAY (EXACTLY as written, ALL CAPS, centered):
"{display_text}"

The text should be LARGE, BOLD, and take up most of the image. This is a hook slide - the text IS the content.
Think: viral TikTok carousel first slide that makes people swipe.

Format: Vertical 9:16 mobile format (1080x1920 style proportions)
Style: Dark aesthetic, scroll-stopping, modern TikTok slideshow look
```

**Person Slide Prompt:**
```
Create a TikTok slideshow image featuring {person_name}.

BACKGROUND:
{visual_description if visual_description else f"Dark, moody portrait-style background suggesting {person_name}. Classical/historical aesthetic with dark shadows and subtle warm highlights."}
The background should be visible but NOT compete with the text overlay.

{tiktok_text_style}

TEXT TO DISPLAY (in this exact layout):

TOP OF IMAGE:
"#{slide_number}" - Large, bold white text

CENTER OF IMAGE:
"{display_text}" - Large, bold white text (this is the main name/title)

LOWER CENTER (if subtitle provided):
"{subtitle}" - Smaller white text, still bold and readable

Layout like a TikTok slideshow: numbered list item with the main subject and a punchy one-liner underneath.

Format: Vertical 9:16 mobile format
Style: Dark aesthetic, TikTok carousel style, modern and clean typography
```

**Quote Slide Prompt:**
```
Create a TikTok slideshow QUOTE image.

BACKGROUND:
{visual_description if visual_description else "Dark, atmospheric, contemplative background. Abstract or minimal so the quote can shine."}

{tiktok_text_style}

TEXT TO DISPLAY:

TOP:
"#{slide_number}" - in bold white

CENTER (the quote):
"{subtitle}" - in elegant but bold white text, slightly larger

BOTTOM ATTRIBUTION:
"— {display_text}" - smaller white text

This is a quote slide - the words are the star. Make them crisp and impactful.

Format: Vertical 9:16 mobile format
Style: Inspirational TikTok quote post aesthetic
```

**Outro Slide Prompt:**
```
Create a TikTok slideshow OUTRO/call-to-action image.

BACKGROUND:
{visual_description if visual_description else "Dark, powerful, cinematic background. Could be abstract gradients or atmospheric imagery."}

{tiktok_text_style}

TEXT TO DISPLAY (centered, impactful):
"{display_text}"
{f'"{subtitle}"' if subtitle else ''}

This is the closing slide - should leave an impression or prompt action (follow, like, share).

Format: Vertical 9:16 mobile format
Style: TikTok carousel closing slide, bold and memorable
```

**Key Differences:**
- Multiple slide type templates (hook, person, quote, outro, generic)
- White text with shadow (not golden metallic)
- Modern TikTok/CapCut aesthetic (not classical Renaissance)
- Layout instructions for multi-element slides

---

### 11. TikTok Background Image (`tiktok_slideshow.py`)

**Model:** `fal-ai/flux/schnell` (fal) or `dall-e-3` (OpenAI)  
**Used by:** `_generate_background_prompt()` / `_generate_background_fal()` / `_generate_background_openai()`  
**Purpose:** Generate background images ONLY (text added programmatically)

**Base Style (used in all types):**
```
STYLE REQUIREMENTS:
- Vertical format (9:16 aspect ratio, 1080x1920 pixels)
- TikTok/Instagram aesthetic - scroll-stopping, visually striking
- Clean composition with space for text overlay in center
- High contrast, bold colors OR moody dark tones
- Professional, cinematic quality
- Simple, focused - ONE main subject, not cluttered

CRITICAL: 
- Do NOT include any text, words, letters, numbers, or typography
- Do NOT include watermarks or logos
- This is a BACKGROUND ONLY - text will be added separately
- Leave the CENTER of the image relatively clean for text overlay
```

**Hook Background:**
```
Create a POWERFUL, scroll-stopping background image for a viral TikTok slideshow hook.

SUBJECT: {visual_description if visual_description else f"Epic, dramatic scene related to: {subject}"}

MOOD: Epic, mysterious, makes you STOP scrolling
- Think: movie poster energy, dramatic lighting
- Could be: silhouettes, dramatic skies, iconic imagery
- Feel: "Something important is about to be revealed"

{base_style}

Make it feel like the opening shot of an epic documentary or movie trailer.
```

**Person Background:**
```
Create an artistic background image featuring or representing: {person_name if person_name else display_text}

VISUAL: {visual_description if visual_description else f"Artistic representation of {person_name or display_text} - silhouette, stylized portrait, or scene from their era"}

GUIDELINES FOR PERSON-BASED SLIDES:
- If ancient philosopher (Marcus Aurelius, Socrates, etc): Classical art style, marble textures, Roman/Greek setting, warm golden candlelight
- If modern figure (Steve Jobs, Elon Musk, etc): Clean minimalist style, modern aesthetic, their iconic look/setting
- If religious/spiritual (Buddha, Confucius): Serene, peaceful, warm tones, nature elements
- Make the person RECOGNIZABLE through their iconic elements (Jobs = black turtleneck, Aurelius = Roman emperor robes, etc.)

{base_style}
```

**Lesson/Reason Background:**
```
Create an aesthetic background that visually represents this concept:

CONCEPT: {visual_description if visual_description else f"Visual metaphor for: {display_text}"}

MOOD: Thoughtful, inspiring, makes the viewer pause and think
- Simple, clean composition
- Could be: metaphorical imagery, symbolic objects, atmospheric scenes
- The image should SUPPORT the message, not distract from it

{base_style}

Think: What image would make this lesson/reason hit harder?
```

**Quote Background:**
```
Create a contemplative, minimalist background for a philosophical quote.

VISUAL: {visual_description if visual_description else "Soft, atmospheric scene - gradients, silhouettes, or nature that evokes deep thinking"}

MOOD: Peaceful, contemplative, lets the words shine
- Keep it SIMPLE - the quote is the star
- Soft lighting, muted or warm tones
- Could be: abstract gradients, peaceful landscapes, minimal scenes

{base_style}
```

**Outro Background:**
```
Create an inspiring, powerful closing image for a TikTok slideshow.

VISUAL: {visual_description if visual_description else "Inspiring scene - figure at sunrise, path into light, or uplifting imagery suggesting possibility and action"}

MOOD: Hopeful, inspiring, calls to action
- Feel like a NEW BEGINNING
- Could be: sunrise, open road, figure facing horizon, light breaking through
- Makes the viewer want to TAKE ACTION

{base_style}
```

**Key Differences:**
- Uses Flux Schnell (faster model) or DALL-E 3
- NO TEXT in image - text added later via `text_overlay.py`
- Explicit "leave center clean for text" instruction
- Style varies by slide type (person, lesson, quote, etc.)

---

## 🎬 VIDEO GENERATION PROMPTS

### 12. Image-to-Video Transition (`fal_video_generator.py`)

**Model:** `fal-ai/minimax/hailuo-02/standard/image-to-video`  
**Used by:** `generate_transition_video()`  
**Purpose:** Create smooth video transitions between two images

```
Artistic cinematic transition in a dark, candlelit ancient chamber, \
historical documentary style with high contrast and warm golden tones. \
{scene_description}. \
The scene remains still as analog TV static interference slowly builds, \
white noise pixels flickering and scrambling in black-and-white static bursts, \
like an old television losing signal, with scan lines and horizontal hold \
glitches intensifying. The camera slowly and smoothly dollies in. \
Photorealistic oil painting texture, epic historical atmosphere, \
deliberate and precise visual effects only.
```

**Key Features:**
- Used with `image_url` (start frame) and `end_image_url` (end frame)
- Creates TV static interference effect as transition
- Camera dolly in motion
- Classical/documentary aesthetic
- 5-6 second clips

---

## 📊 Prompt Comparison Summary

| Prompt | Model | Output Type | Text in Image? | Style |
|--------|-------|-------------|----------------|-------|
| List Script | Gemini 3 Pro | JSON (script) | N/A | Viral/dramatic |
| Narrative Script | Gemini 3 Pro | JSON (script) | N/A | Story/dramatic |
| Slideshow Script | Gemini 3 Pro | JSON (script) | N/A | TikTok hooks |
| Scene Analysis | Gemini 2.0 Flash | JSON (prompts) | N/A | Classical art |
| Caption | GPT-5 Nano | Text (caption) | N/A | Conversational |
| Basic Image | Gemini 3 Pro Image | Image | No | Classical painting |
| Smart Image | Gemini 3 Pro Image | Image | Yes (golden) | Renaissance/Baroque |
| OpenAI Image | DALL-E 3 / GPT-Image | Image | No | Caravaggio style |
| GPT15 Image | GPT Image 1.5 | Image | Yes (golden) | Classical + bold text |
| Slideshow Slide | GPT Image 1.5 | Image | Yes (white) | TikTok/CapCut modern |
| Background Only | Flux/DALL-E | Image | No | Clean for overlay |
| Video Transition | MiniMax Hailuo-02 | Video | N/A | Documentary + static |

---

## 🔧 When to Use Which Prompt

### For Video Pipeline (`pipeline.py`):
1. **Script**: Use `generate_timed_script()` → auto-detects list vs narrative
2. **Images**: Use `GPTImageGenerator` (gpt15) for best text overlays
3. **Video**: Use `FalVideoGenerator` for transitions
4. **Audio**: Use `VoiceGenerator` for timestamps

### For Slideshow Pipeline (`tiktok_slideshow.py`):
1. **Script**: Use `generate_slideshow_script()` for static slides
2. **Backgrounds**: Use `_generate_background_fal()` or `_generate_background_openai()`
3. **Text**: Use `TextOverlay` to burn text programmatically (best control)

### For Captions:
- Use `CaptionGenerator` with GPT-5 Nano (cheap + fast)

---

## 📝 Notes

1. **Word Counts**: Video scripts enforce 12-15 words per scene for audio sync
2. **Aspect Ratio**: All images target 9:16 vertical (1080x1920)
3. **Text Styling**: Two approaches:
   - AI-generated: Golden metallic text in image (gpt_image_generator, smart_image_generator)
   - Programmatic: White text via Pillow (text_overlay.py) - more control
4. **Philosophy Focus**: All prompts emphasize connecting content to philosophy/ancient wisdom
5. **Fallback Models**: Gemini 3 Pro → Gemini 2.0 Flash Exp (automatic)
