from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from typing import Dict, List

from gemini_handler import GeminiHandler
from smart_image_generator import SmartImageGenerator
from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler

app = FastAPI(title="Philosophy Video Generator")

# Initialize components
gemini = GeminiHandler()
image_gen = SmartImageGenerator()
voice_gen = VoiceGenerator()
video_assembler = VideoAssembler()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create templates directory and basic HTML
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

class PhilosophyVideoGenerator:
    def __init__(self):
        self.gemini = GeminiHandler()
        self.image_gen = SmartImageGenerator()
        self.voice_gen = VoiceGenerator()
        self.video_assembler = VideoAssembler()
    
    def generate_complete_video(self, topic: str, voice_id: str = None) -> Dict:
        """Complete pipeline from topic to final video"""
        
        print(f"🎬 Starting video generation for topic: {topic}")
        
        # Step 1: Generate story script with scenes
        print("📝 Generating story script...")
        story_data = self.gemini.generate_philosophy_story(topic)
        if not story_data:
            return {"error": "Failed to generate story"}
        
        print(f"✅ Generated {len(story_data.get('scenes', []))} scenes")
        
        # Step 2: Generate voiceover
        print("🎤 Generating voiceover...")
        script = story_data.get('script', '')
        audio_path = self.voice_gen.generate_voiceover(script, voice_id, f"{topic.replace(' ', '_')}_narration.mp3")
        if not audio_path:
            return {"error": "Failed to generate voiceover"}
        
        print(f"✅ Generated audio: {audio_path}")
        
        # Step 3: Generate images for each scene
        print("🎨 Generating scene images...")
        scenes = story_data.get('scenes', [])
        image_paths = self.image_gen.generate_all_images(story_data, scenes)
        if not image_paths:
            return {"error": "Failed to generate images"}
        
        print(f"✅ Generated {len(image_paths)} images")
        
        # Step 4: Assemble final video
        print("🎬 Assembling final video...")
        video_path = self.video_assembler.create_philosophy_video(
            scenes, audio_path, image_paths, topic
        )
        if not video_path:
            return {"error": "Failed to assemble video"}
        
        print(f"✅ Video completed: {video_path}")
        
        # Step 5: Optimize for TikTok
        print("📱 Optimizing for TikTok...")
        optimized_path = self.video_assembler.optimize_for_tiktok(video_path)
        
        return {
            "success": True,
            "story_data": story_data,
            "audio_path": audio_path,
            "image_paths": image_paths,
            "video_path": video_path,
            "optimized_path": optimized_path,
            "topic": topic
        }

# Global generator instance
generator = PhilosophyVideoGenerator()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_video(topic: str = Form(...), voice_id: str = Form(default=None)):
    """Generate complete philosophy video from topic"""
    
    try:
        result = generator.generate_complete_video(topic, voice_id)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/preview/{topic}")
async def preview_story(topic: str):
    """Preview generated story without creating full video"""
    
    try:
        story_data = gemini.generate_philosophy_story(topic)
        return story_data
    except Exception as e:
        return {"error": str(e)}

@app.get("/voices")
async def get_voices():
    """Get available voice options"""
    return voice_gen.get_available_voices()

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated video file"""
    
    video_path = f"generated_videos/{filename}"
    if os.path.exists(video_path):
        return FileResponse(video_path, filename=filename)
    else:
        return {"error": "File not found"}

@app.get("/topics")
async def get_topic_suggestions():
    """Get suggested philosophy topics"""
    return {
        "ancient_philosophy": [
            "Plato's Cave Allegory",
            "Socrates' Last Day",
            "The Trial of Socrates",
            "Aristotle's Golden Mean",
            "Stoic Philosophy and Marcus Aurelius",
            "Diogenes and Cynicism",
            "The Oracle at Delphi"
        ],
        "existentialism": [
            "Camus and the Absurd",
            "Sartre's Cafe de Flore",
            "Nietzsche's Eternal Recurrence",
            "Kierkegaard's Leap of Faith",
            "The Myth of Sisyphus"
        ],
        "eastern_philosophy": [
            "Buddha's Enlightenment",
            "Lao Tzu and the Tao",
            "Confucius and Social Harmony",
            "Zen and the Art of Being",
            "The Middle Way"
        ],
        "modern_philosophy": [
            "Descartes' Cogito",
            "Kant's Categorical Imperative",
            "Hume's Problem of Induction",
            "Berkeley's Idealism",
            "Mill's Utilitarianism"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Philosophy Video Generator...")
    print("📍 Access the web interface at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)