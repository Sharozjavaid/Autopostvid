# 🧠 Philosophy Video Generator

Automatically create engaging TikTok-style philosophy videos using AI. Input a philosophical topic and get a complete video with narration, classical imagery, and optimized formatting.

## Features

- **Intelligent Story Generation**: Gemini 3 Pro creates engaging philosophy stories
- **Scene-Based Image Creation**: AI generates classical, dark, mysterious images for each story beat  
- **Professional Voiceover**: ElevenLabs integration with multiple voice options
- **TikTok Optimization**: Vertical video format optimized for social media
- **Semi-Automated Workflow**: Review scripts and images before final video assembly

## Tech Stack

- **AI Models**: Google Gemini 3 Pro (text + image generation)
- **Voice**: ElevenLabs API
- **Video Processing**: MoviePy
- **Backend**: FastAPI + Python
- **Frontend**: Modern HTML/CSS/JavaScript

## Quick Start

1. **Install Dependencies**
   ```bash
   cd philosophy_video_generator
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Add your ElevenLabs API key to `.env` file
   - Google API key is already configured

3. **Run the Application**
   ```bash
   # Web Interface
   python main.py
   
   # Test Generation
   python run.py
   ```

4. **Access Web Interface**
   - Open: http://localhost:8000
   - Select a philosophy topic
   - Choose voice settings
   - Generate video!

## Usage Examples

### Web Interface
1. Navigate to http://localhost:8000
2. Enter topic: "Plato's Cave Allegory" 
3. Select voice (optional)
4. Click "Generate Philosophy Video"
5. Wait 2-3 minutes for processing
6. Download TikTok-optimized video

### Programmatic Usage
```python
from main import PhilosophyVideoGenerator

generator = PhilosophyVideoGenerator()
result = generator.generate_complete_video("Socrates' Death")

if result['success']:
    print(f"Video saved: {result['optimized_path']}")
```

## Suggested Topics

### Ancient Philosophy
- Plato's Cave Allegory
- Socrates' Last Day  
- Marcus Aurelius and Stoicism
- Diogenes and Cynicism
- Aristotle's Golden Mean

### Eastern Philosophy
- Buddha's Enlightenment
- Lao Tzu and the Tao
- Zen and the Art of Being
- Confucius and Harmony

### Existentialism
- Camus and the Absurd
- Nietzsche's Eternal Recurrence
- The Myth of Sisyphus
- Sartre's Bad Faith

## Output Structure

Generated videos include:
- **Duration**: 50-60 seconds (optimal for TikTok)
- **Format**: Vertical 9:16 (1080x1920)
- **Audio**: Professional AI narration
- **Visuals**: 6-8 classical/dark philosophical images
- **Style**: Engaging, mysterious, educational
- **Promotion**: Subtle philosophy app promotion

## File Structure

```
philosophy_video_generator/
├── main.py                 # FastAPI web application
├── gemini_handler.py       # Gemini 3 Pro integration
├── image_generator.py      # Classical image generation
├── voice_generator.py      # ElevenLabs voice synthesis  
├── video_assembler.py      # MoviePy video compilation
├── run.py                  # Test runner
├── requirements.txt        # Python dependencies
├── .env                    # API keys configuration
├── templates/              # HTML templates
│   └── index.html         # Web interface
├── generated_images/       # Output images
├── generated_audio/        # Output audio files
└── generated_videos/       # Final video outputs
```

## API Endpoints

- `GET /` - Web interface
- `POST /generate` - Generate complete video
- `GET /preview/{topic}` - Preview story without video
- `GET /voices` - Available voice options  
- `GET /topics` - Suggested philosophy topics
- `GET /download/{filename}` - Download generated video

## Customization

### Voice Options
- Adam (Default) - Deep, authoritative
- Alice - Clear, professional female
- Antoni - Warm, narrative male
- Rachel - Calm, soothing female
- And more...

### Image Styles
- Classical Renaissance/Baroque aesthetic
- Dark, moody atmosphere
- Philosophical symbolism
- Dramatic chiaroscuro lighting
- Golden highlights and shadows

### Story Tone
- 8th grade reading level
- Wise mentor style
- Second-person perspective
- Hook-optimized for engagement
- Philosophy app promotion integration

## Troubleshooting

**Missing API Keys**: Ensure `.env` file contains valid ElevenLabs API key
**Image Generation**: Placeholder images created if Gemini image API unavailable
**Video Rendering**: Requires FFmpeg installation for MoviePy
**Memory Usage**: Large videos may require additional RAM

## Philosophy App Integration

Generated videos include subtle promotion of a philosophy learning app where users can:
- Talk to AI philosophers
- Learn about philosophical schools
- Explore ancient wisdom
- Engage with philosophical concepts

Perfect for marketing philosophical education platforms!