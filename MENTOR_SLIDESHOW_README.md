# Philosophical Mentor Slideshow Generator

## Overview

The `generate_mentor_slideshow()` method creates scripts in a **direct, no-nonsense motivational tone** — like a philosophical mentor texting hard truths to someone ready to level up their thinking.

## Writing Style

- **Voice**: Second person "you" with occasional "we" for solidarity
- **Tone**: Direct, confrontational-then-empowering
- **Reading Level**: 6th-7th grade
- **Sentence Structure**: 
  - Short, punchy 5-10 word sentences
  - Occasional longer reflective statements
  - Sentence fragments for impact
- **Formatting**:
  - Periods for emphasis
  - Ellipses (...) for contemplative pauses
  - Occasional ALL CAPS for key concepts
  - Rhetorical questions to challenge assumptions

## Slide Structure

### Slide 1: The Hook
- **1 text item only**
- **6-10 words maximum**
- Large font
- Provocative, challenging, or deeply relatable
- Examples:
  - "Your mind is lying to you. Again."
  - "Nobody taught you how to think."
  - "Stop running. Start thinking."

### Slides 2-6: The Content (5 slides)
Each slide has **EXACTLY 3 text items**:

1. **Main insight** (medium-large font): 6-12 words
   - A philosophical insight OR mental trap
   - Direct and punchy
   - Example: "You're chasing happiness. That's why you don't have it."

2. **"What it does:"** (small font): 3-6 words
   - Brief explanation of the psychological mechanism
   - Must start with "What it does:"
   - Example: "What it does: Keeps you stuck in loops."

3. **"Why it matters:"** (small font): 10-20 words
   - Connects to personal growth or philosophical understanding
   - Must start with "Why it matters:"
   - Example: "Why it matters: When you stop chasing, you create space for peace to find you."

### Slide 7: The Outro
**2-3 text items**:

1. **Rhetorical question or statement** (medium font): 6-10 words
   - Challenges reflection
   - Example: "What are you really running from?"

2. **Call to action** (small font): 8-15 words
   - Encourages saving, reflecting, or continuing
   - Example: "Save this. Read it again when your mind starts lying."

3. **Philosophical truth** (small font, optional): 8-12 words
   - Encouraging final thought
   - Example: "The truth was always inside you. You just forgot."

## How to Test

### Quick Test
```bash
python test_mentor_slideshow.py
```

This will:
1. Generate a mentor-style slideshow script
2. Display the full structure
3. Validate the format
4. Save the JSON output to a file

### Custom Topic Test
```python
from gemini_handler import GeminiHandler

handler = GeminiHandler()
script = handler.generate_mentor_slideshow("Why you can't focus")

# Access the structure
for slide in script['slides']:
    slide_num = slide['slide_number']
    slide_type = slide['slide_type']  # 'hook', 'content', or 'outro'
    text_items = slide['text_items']
    
    for item in text_items:
        text = item['text']
        font_size = item['font_size']  # 'large', 'medium', 'medium-large', 'small'
        label = item.get('label', '')   # 'What it does:' or 'Why it matters:'
        word_count = item['word_count']
```

## JSON Output Structure

```json
{
  "title": "Short catchy title",
  "topic": "Your input topic",
  "content_type": "mentor_slideshow",
  "writing_style": "philosophical_mentor",
  "total_slides": 7,
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "hook",
      "text_items": [
        {
          "text": "Your mind is lying to you. Again.",
          "font_size": "large",
          "word_count": 7
        }
      ],
      "visual_description": "Dark moody background..."
    },
    {
      "slide_number": 2,
      "slide_type": "content",
      "text_items": [
        {
          "text": "You scroll to escape. But escape from what?",
          "font_size": "medium-large",
          "word_count": 9
        },
        {
          "label": "What it does:",
          "text": "Numbs the real questions.",
          "font_size": "small",
          "word_count": 4
        },
        {
          "label": "Why it matters:",
          "text": "Every swipe is a vote against facing yourself...",
          "font_size": "small",
          "word_count": 18
        }
      ],
      "visual_description": "Person illuminated only by phone screen..."
    }
  ]
}
```

## Where It's Implemented

**File**: `gemini_handler.py`

**Method**: `GeminiHandler.generate_mentor_slideshow(topic: str)`

**Location**: Around line 433 (added before the existing `generate_slideshow_script` method)

## Integration with Your Pipeline

To use this in your existing slideshow generation pipeline, you'll need to:

1. **Choose the method** based on content type:
   ```python
   # Old style (person-based lists, arguments)
   script = handler.generate_slideshow_script(topic)
   
   # New mentor style (psychological insights, mental traps)
   script = handler.generate_mentor_slideshow(topic)
   ```

2. **Update your image generation** to handle the new structure:
   ```python
   # Content slides now have multiple text items with different font sizes
   for slide in script['slides']:
       if slide['slide_type'] == 'content':
           text_items = slide['text_items']
           # Item 1: Main insight (medium-large font)
           # Item 2: "What it does:" label (small font)
           # Item 3: "Why it matters:" explanation (small font)
   ```

3. **Adjust text layout** in your slide renderer to accommodate:
   - Multiple font sizes on the same slide
   - Labels ("What it does:", "Why it matters:")
   - Proper spacing between the 3 sections

## Best Topics for Mentor Style

This format works best for:

- Mental traps and cognitive biases
- Self-awareness and introspection
- Modern struggles (scrolling, distraction, comparison)
- Philosophical wisdom applied to everyday life
- Questioning assumptions and beliefs

Examples:
- "Why you can't think clearly"
- "The truth about your overthinking"
- "5 mental traps keeping you stuck"
- "Why chasing happiness makes you miserable"
- "The philosophy of letting go"
- "Stop avoiding. Start feeling."

## Next Steps

1. **Test the generator**: Run `python test_mentor_slideshow.py`
2. **Review the output**: Check the generated JSON file
3. **Update your slide renderer**: Modify to handle the new multi-text-item structure
4. **Integrate into pipeline**: Add logic to choose between mentor style and classic style
5. **Test with real images**: Generate actual slide images with the new format
