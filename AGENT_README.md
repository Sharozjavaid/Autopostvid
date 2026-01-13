# Marketing Agent Chat Interface

A conversational AI agent for creating viral TikTok philosophy slideshows through natural language.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (add to `.env`):
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_API_KEY=your_gemini_api_key
   FAL_KEY=your_fal_ai_key  # For image generation
   ELEVENLABS_API_KEY=your_elevenlabs_key  # For voiceover
   EMAIL_USER=your_email@gmail.com  # For sending videos
   EMAIL_PASSWORD=your_app_password
   ```

3. **Run the web interface:**
   ```bash
   python3 agent_app.py
   ```
   
   Open http://localhost:5001 in your browser.

4. **Or run in terminal mode:**
   ```bash
   python3 agent_runner.py
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Chat Panel    │  │  Live Preview   │  │ Activity Log │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Runner (Claude)                     │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Claude Sonnet  │  │  Memory Manager │                   │
│  │   (Anthropic)   │  │   (Persistent)  │                   │
│  └─────────────────┘  └─────────────────┘                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Tool Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Tools                             │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ GeminiHandler │  │ TikTokSlides  │  │  VoiceGenerator  │ │
│  │  (Scripts)    │  │  (Images)     │  │   (ElevenLabs)   │ │
│  └───────────────┘  └───────────────┘  └──────────────────┘ │
│  ┌───────────────┐  ┌───────────────┐                       │
│  │ VideoAssembler│  │  EmailSender  │                       │
│  │   (moviepy)   │  │    (SMTP)     │                       │
│  └───────────────┘  └───────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Files Created

| File | Purpose |
|------|---------|
| `agent_tools.py` | Tool definitions wrapping existing modules |
| `agent_memory.py` | Memory manager (summary + recent + project state) |
| `agent_runner.py` | Claude SDK client with tool server |
| `agent_app.py` | Flask web app with WebSocket |
| `templates/agent_chat.html` | Chat UI with live preview |
| `memory/` | Directory for persistent memory files |

## Workflow Example (Interactive)

1. **You**: "Make a script about 5 stoic philosophers"
2. **Agent**: Calls `generate_script` → script JSON created
3. **You**: "Generate just the first slide"
4. **Agent**: Calls `generate_single_slide(slide_index=0)` → image appears in preview
5. **You**: "Try it with the Cinzel font"
6. **Agent**: Calls `change_font_style(font_name="cinzel")` → image re-renders
7. **You**: "Looks good, generate the rest"
8. **Agent**: Calls `generate_all_slides` → all slides generated
9. **You**: "Turn it into a video and email it to me"
10. **Agent**: Calls `create_video_from_slides`, then `send_email_with_content`

## Autonomous Workflow (Self-Operating)

When running autonomously, the agent:

1. **Checks past learnings**: `get_learnings(category="fonts")` → "Cinzel works for Roman topics"
2. **Checks performance**: `get_best_performing_content()` → "Stoic content gets 12% engagement"
3. **Generates content**: `generate_script("Marcus Aurelius quotes")`
4. **Creates slides**: `generate_single_slide(slide_index=0)`
5. **Self-reviews**: `review_slide_quality(slide_index=0)` → "Score: 7.5/10, readability could be better"
6. **Iterates**: `compare_slides(slide_index=0, variations=[{font: "bebas"}, {font: "cinzel"}])`
7. **Picks best**: Agent selects the highest-scoring variation
8. **Completes all slides**: `generate_all_slides()`
9. **Stores learning**: `store_learning(category="fonts", learning="Bebas worked better for quote slideshows")`

## Available Tools

### Content Creation
| Tool | Description |
|------|-------------|
| `generate_script` | Generate slideshow script from topic |
| `generate_single_slide` | Generate one slide (background + text) |
| `generate_all_slides` | Generate all slides for current script |
| `change_font_style` | Re-render slide with different font |
| `list_available_fonts` | Get available font options |
| `create_video_from_slides` | Create video with voiceover |
| `send_email_with_content` | Email the finished video |
| `get_project_state` | Get current project data |

### Autonomous Review (NEW)
| Tool | Description |
|------|-------------|
| `review_slide_quality` | **Vision AI** - Analyze a slide and rate quality (readability, appeal, etc.) |
| `review_all_slides` | Review all slides and identify ones to regenerate |
| `compare_slides` | A/B test different font/style variations |

### Learning & Memory (NEW)
| Tool | Description |
|------|-------------|
| `store_learning` | Store insights about what works (fonts, topics, styles) |
| `get_learnings` | Retrieve past learnings before creating content |
| `store_performance_data` | Record TikTok metrics (manual until API integration) |
| `get_performance_data` | Get past performance metrics |
| `get_best_performing_content` | Analyze top performers to find patterns |

## Available Fonts

- **bebas**: Bold display font - punchy headlines
- **cinzel**: Roman/classical capitals - ancient wisdom vibes
- **cormorant**: Elegant italic - @philosophaire style
- **montserrat**: Clean modern sans-serif
- **oswald**: Condensed sans-serif - impactful
- **montserrat-italic**: Modern italic

## Visual Styles

- **modern**: Clean with drop shadows (default)
- **elegant**: Italic fonts, sophisticated look
- **philosophaire**: Classic style like @philosophaire Instagram

## Memory System

The agent maintains persistent memory:

```
memory/
  conversation_summary.txt    # Rolling summary of older context
  recent_messages.json        # Last 20 messages (full content)
  current_project.json        # Active script, slides, paths
  insights.txt                # Learnings the agent notes
```

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Add your Anthropic API key to the `.env` file

**Images not generating**
- Check `FAL_KEY` is set for fal.ai image generation
- Or use `skip_image_generation=True` for solid backgrounds

**Voiceover failing**
- Ensure `ELEVENLABS_API_KEY` is set

**Email not sending**
- Set `EMAIL_USER` and `EMAIL_PASSWORD` (use Gmail app password)
