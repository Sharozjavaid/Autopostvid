#!/usr/bin/env python3
"""
Agent Tools - Wraps existing modules as callable tools for the Claude agent.

This module exposes the philosophy video generator's functionality as 
structured tool functions that can be called by the Claude agent.

Each tool:
1. Has a clear name and description
2. Accepts JSON-serializable parameters
3. Returns JSON-serializable results
4. Handles errors gracefully

Usage:
    from agent_tools import AgentTools
    
    tools = AgentTools()
    result = tools.generate_script("5 philosophers who changed the world")
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# Import from central config - single source of truth
# To change the model, edit: backend/app/config.py -> CLAUDE_MODEL
# =============================================================================
try:
    from backend.app.config import CLAUDE_MODEL
except ImportError:
    # Fallback for standalone CLI usage
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


class AgentTools:
    """
    Tool registry that wraps existing modules for Claude agent use.
    
    All tools return dictionaries with:
    - success: bool
    - data: the actual result data
    - error: error message if failed
    """
    
    def __init__(self, output_dir: str = "generated_slideshows"):
        """Initialize with output directories."""
        self.output_dir = output_dir
        self.backgrounds_dir = os.path.join(output_dir, "backgrounds")
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.backgrounds_dir, exist_ok=True)
        
        # Current project state (shared across tools)
        self.current_project = None
        
        print("🛠️ AgentTools initialized")
    
    # ==================== SCRIPT GENERATION ====================
    
    def generate_script(self, topic: str) -> Dict[str, Any]:
        """
        Generate a slideshow script from a topic.
        
        This creates the content structure for a TikTok slideshow:
        - Hook slide (scroll-stopping opening)
        - Content slides (lessons, people, reasons)
        - Outro slide (call to action)
        
        Args:
            topic: The topic for the slideshow (e.g., "5 philosophers who changed the world")
        
        Returns:
            {
                "success": True/False,
                "script": {...script data...},
                "slide_count": 6,
                "title": "...",
                "error": "..." (if failed)
            }
        """
        try:
            from gemini_handler import GeminiHandler
            
            handler = GeminiHandler()
            script = handler.generate_slideshow_script(topic)
            
            if not script:
                return {
                    "success": False,
                    "error": "Failed to generate script - check Gemini API key"
                }
            
            # Store as current project
            self.current_project = {
                "script": script,
                "topic": topic,
                "slides": script.get("slides", []),
                "title": script.get("title", topic),
                "created_at": datetime.now().isoformat(),
                "image_paths": [],
                "background_paths": []
            }
            
            # Save script to file
            safe_name = self._safe_filename(script.get("title", topic))
            script_path = os.path.join(self.output_dir, f"{safe_name}_script.json")
            with open(script_path, 'w') as f:
                json.dump(script, f, indent=2)
            
            return {
                "success": True,
                "script": script,
                "slide_count": len(script.get("slides", [])),
                "title": script.get("title", topic),
                "script_path": script_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== SLIDE GENERATION ====================
    
    def generate_single_slide(
        self,
        slide_index: int,
        font_name: Optional[str] = None,
        visual_style: str = "modern",
        skip_image_generation: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a single slide (background image + text overlay).
        
        Requires a script to be generated first via generate_script().
        
        Args:
            slide_index: Which slide to generate (0-based)
            font_name: Font to use (e.g., "bebas", "cinzel", "cormorant")
            visual_style: Style preset ("modern", "elegant", "philosophaire")
            skip_image_generation: If True, uses solid background (faster)
        
        Returns:
            {
                "success": True/False,
                "image_path": "path/to/slide.png",
                "background_path": "path/to/bg.png",
                "slide_data": {...},
                "error": "..." (if failed)
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No script loaded. Call generate_script() first."
                }
            
            slides = self.current_project.get("slides", [])
            if slide_index >= len(slides):
                return {
                    "success": False,
                    "error": f"Slide index {slide_index} out of range. Script has {len(slides)} slides."
                }
            
            from tiktok_slideshow import TikTokSlideshow
            
            slideshow = TikTokSlideshow(output_dir=self.output_dir)
            slide = slides[slide_index]
            title = self.current_project.get("title", "slideshow")
            
            result = slideshow.generate_single_slide(
                slide=slide,
                slide_index=slide_index,
                slideshow_title=title,
                skip_image_generation=skip_image_generation,
                font_name=font_name,
                visual_style=visual_style
            )
            
            # Update project state
            if result.get("success"):
                # Ensure lists are long enough
                while len(self.current_project["image_paths"]) <= slide_index:
                    self.current_project["image_paths"].append(None)
                while len(self.current_project["background_paths"]) <= slide_index:
                    self.current_project["background_paths"].append(None)
                
                self.current_project["image_paths"][slide_index] = result.get("image_path")
                self.current_project["background_paths"][slide_index] = result.get("background_path")
            
            return {
                "success": result.get("success", False),
                "image_path": result.get("image_path"),
                "background_path": result.get("background_path"),
                "slide_index": slide_index,
                "slide_data": slide
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_all_slides(
        self,
        font_name: Optional[str] = None,
        visual_style: str = "modern",
        skip_image_generation: bool = False
    ) -> Dict[str, Any]:
        """
        Generate all slides for the current script.
        
        Args:
            font_name: Font to use for all slides
            visual_style: Style preset
            skip_image_generation: If True, uses solid backgrounds
        
        Returns:
            {
                "success": True/False,
                "image_paths": ["path1.png", "path2.png", ...],
                "slide_count": 6,
                "error": "..." (if failed)
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No script loaded. Call generate_script() first."
                }
            
            slides = self.current_project.get("slides", [])
            results = []
            failed = []
            
            for i in range(len(slides)):
                result = self.generate_single_slide(
                    slide_index=i,
                    font_name=font_name,
                    visual_style=visual_style,
                    skip_image_generation=skip_image_generation
                )
                
                if result.get("success"):
                    results.append(result.get("image_path"))
                else:
                    failed.append(i)
            
            return {
                "success": len(failed) == 0,
                "image_paths": results,
                "slide_count": len(results),
                "failed_slides": failed if failed else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def change_font_style(
        self,
        slide_index: int,
        font_name: str,
        visual_style: str = "modern"
    ) -> Dict[str, Any]:
        """
        Re-render a slide with a different font.
        
        Uses the existing background image but re-applies text with new font.
        
        Args:
            slide_index: Which slide to re-render
            font_name: New font name (e.g., "bebas", "cinzel", "cormorant", "montserrat")
            visual_style: Style preset ("modern", "elegant", "philosophaire")
        
        Returns:
            {
                "success": True/False,
                "image_path": "path/to/slide.png",
                "font_used": "bebas",
                "error": "..." (if failed)
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded. Call generate_script() first."
                }
            
            slides = self.current_project.get("slides", [])
            if slide_index >= len(slides):
                return {
                    "success": False,
                    "error": f"Slide index {slide_index} out of range."
                }
            
            background_paths = self.current_project.get("background_paths", [])
            if slide_index >= len(background_paths) or not background_paths[slide_index]:
                return {
                    "success": False,
                    "error": f"No background exists for slide {slide_index}. Generate the slide first."
                }
            
            from tiktok_slideshow import TikTokSlideshow
            
            slideshow = TikTokSlideshow(output_dir=self.output_dir)
            slide = slides[slide_index]
            title = self.current_project.get("title", "slideshow")
            bg_path = background_paths[slide_index]
            
            safe_name = self._safe_filename(title)
            output_path = os.path.join(self.output_dir, f"{safe_name}_slide_{slide_index}.png")
            
            final_path = slideshow._burn_text_onto_slide(
                background_path=bg_path,
                slide=slide,
                output_path=output_path,
                font_name=font_name,
                visual_style=visual_style
            )
            
            # Update project state
            self.current_project["image_paths"][slide_index] = final_path
            
            return {
                "success": True,
                "image_path": final_path,
                "font_used": font_name,
                "slide_index": slide_index
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== FONT UTILITIES ====================
    
    def list_available_fonts(self) -> Dict[str, Any]:
        """
        Get list of all available fonts for styling.
        
        Returns:
            {
                "success": True,
                "fonts": {
                    "bebas": {"name": "Bebas Neue", "description": "...", "category": "display"},
                    ...
                },
                "categories": ["modern", "elegant", "classical", "display"]
            }
        """
        try:
            from text_overlay import TextOverlay
            
            overlay = TextOverlay()
            available = overlay.get_available_fonts()
            
            # Group by category
            categories = {}
            for font_id, font_info in available.items():
                cat = font_info.get("category", "other")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(font_id)
            
            return {
                "success": True,
                "fonts": available,
                "categories": list(categories.keys()),
                "fonts_by_category": categories
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== VIDEO CREATION ====================
    
    def create_video_from_slides(
        self,
        audio_text: Optional[str] = None,
        voice_id: Optional[str] = None,
        transition: str = "crossfade",
        transition_duration: float = 0.3
    ) -> Dict[str, Any]:
        """
        Create a video from the generated slides.
        
        Combines slides with voiceover audio (generated from script).
        
        Args:
            audio_text: Custom audio text (defaults to script text)
            voice_id: ElevenLabs voice ID (optional)
            transition: Transition type ("none", "crossfade", "fade_black")
            transition_duration: Duration of transitions in seconds
        
        Returns:
            {
                "success": True/False,
                "video_path": "path/to/video.mp4",
                "audio_path": "path/to/audio.mp3",
                "duration": 60.5,
                "error": "..." (if failed)
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded. Generate slides first."
                }
            
            image_paths = [p for p in self.current_project.get("image_paths", []) if p]
            if not image_paths:
                return {
                    "success": False,
                    "error": "No slides generated. Call generate_all_slides() first."
                }
            
            from voice_generator import VoiceGenerator
            from video_assembler import VideoAssembler
            
            # Prepare script text for audio
            script = self.current_project.get("script", {})
            slides = script.get("slides", [])
            
            if audio_text is None:
                # Build narration from slide content
                audio_parts = []
                for slide in slides:
                    text = slide.get("display_text", "")
                    subtitle = slide.get("subtitle", "")
                    if text:
                        audio_parts.append(text)
                    if subtitle:
                        audio_parts.append(subtitle)
                audio_text = ". ".join(audio_parts)
            
            # Generate voiceover
            voice_gen = VoiceGenerator()
            title = self.current_project.get("title", "video")
            safe_name = self._safe_filename(title)
            audio_filename = f"{safe_name}_narration.mp3"
            
            audio_path = voice_gen.generate_voiceover(
                script=audio_text,
                voice_id=voice_id,
                filename=audio_filename
            )
            
            if not audio_path:
                return {
                    "success": False,
                    "error": "Failed to generate voiceover - check ElevenLabs API key"
                }
            
            # Create scenes for video assembler
            scenes = []
            for i, slide in enumerate(slides):
                scenes.append({
                    "scene_number": i + 1,
                    "text": slide.get("display_text", "") + " " + slide.get("subtitle", ""),
                    "key_concept": slide.get("slide_type", "content")
                })
            
            # Assemble video
            assembler = VideoAssembler()
            video_path = assembler.create_philosophy_video(
                scenes=scenes,
                audio_path=audio_path,
                image_paths=image_paths,
                story_title=title,
                transition=transition,
                transition_duration=transition_duration
            )
            
            if not video_path:
                return {
                    "success": False,
                    "error": "Failed to create video"
                }
            
            self.current_project["video_path"] = video_path
            self.current_project["audio_path"] = audio_path
            
            return {
                "success": True,
                "video_path": video_path,
                "audio_path": audio_path,
                "slide_count": len(image_paths)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== EMAIL ====================
    
    def send_email_with_content(
        self,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send the generated video via email.
        
        Args:
            recipient: Email address (defaults to env RECIPIENT_EMAIL)
            subject: Email subject
            body: Email body text
            caption: TikTok caption to include
        
        Returns:
            {
                "success": True/False,
                "recipient": "email@example.com",
                "video_path": "path/to/video.mp4",
                "error": "..." (if failed)
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded."
                }
            
            video_path = self.current_project.get("video_path")
            if not video_path or not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": "No video created. Call create_video_from_slides() first."
                }
            
            from email_sender import EmailSender
            
            sender = EmailSender()
            title = self.current_project.get("title", "Philosophy Video")
            
            if subject is None:
                subject = f"🎥 Your Video is Ready: {title}"
            
            if body is None:
                body = f"Your philosophy video '{title}' is ready!\n\nGenerated by the Marketing Agent."
            
            success = sender.send_video(
                video_path=video_path,
                recipient=recipient,
                subject=subject,
                body=body,
                caption=caption
            )
            
            return {
                "success": success,
                "recipient": recipient or sender.default_recipient,
                "video_path": video_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PROJECT STATE ====================
    
    def get_project_state(self) -> Dict[str, Any]:
        """
        Get the current project state.
        
        Returns:
            Current project data including script, slides, paths, etc.
        """
        if not self.current_project:
            return {
                "success": False,
                "error": "No project loaded"
            }
        
        return {
            "success": True,
            "project": self.current_project
        }
    
    def load_project(self, script_path: str) -> Dict[str, Any]:
        """
        Load a project from a saved script file.
        
        Args:
            script_path: Path to the script JSON file
        
        Returns:
            {
                "success": True/False,
                "title": "...",
                "slide_count": 6
            }
        """
        try:
            with open(script_path, 'r') as f:
                script = json.load(f)
            
            self.current_project = {
                "script": script,
                "topic": script.get("topic", ""),
                "slides": script.get("slides", []),
                "title": script.get("title", "Loaded Project"),
                "created_at": datetime.now().isoformat(),
                "image_paths": [],
                "background_paths": []
            }
            
            return {
                "success": True,
                "title": self.current_project["title"],
                "slide_count": len(self.current_project["slides"])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== AUTONOMOUS REVIEW TOOLS ====================
    
    def review_slide_quality(
        self,
        slide_index: int,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a generated slide image and rate its quality.
        
        Uses Claude's vision capability to look at the slide and provide
        feedback on composition, readability, visual appeal, etc.
        
        Args:
            slide_index: Which slide to review (0-based)
            criteria: Optional list of criteria to evaluate 
                      (defaults to: readability, visual_appeal, hook_strength, brand_consistency)
        
        Returns:
            {
                "success": True/False,
                "slide_index": 0,
                "image_path": "path/to/slide.png",
                "ratings": {
                    "overall": 8.5,
                    "readability": 9,
                    "visual_appeal": 8,
                    "hook_strength": 8,
                    "brand_consistency": 9
                },
                "feedback": "The text is clear and readable...",
                "suggestions": ["Consider using a bolder font", "..."],
                "should_regenerate": False
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded."
                }
            
            image_paths = self.current_project.get("image_paths", [])
            if slide_index >= len(image_paths) or not image_paths[slide_index]:
                return {
                    "success": False,
                    "error": f"No image for slide {slide_index}. Generate it first."
                }
            
            image_path = image_paths[slide_index]
            slide_data = self.current_project.get("slides", [])[slide_index]
            
            # Default criteria
            if criteria is None:
                criteria = ["readability", "visual_appeal", "hook_strength", "brand_consistency"]
            
            # Load and encode the image for vision API
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Use Anthropic API for vision analysis
            import anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                return {
                    "success": False,
                    "error": "ANTHROPIC_API_KEY not set for vision analysis"
                }
            
            client = anthropic.Anthropic(api_key=api_key)
            
            slide_type = slide_data.get("slide_type", "content")
            display_text = slide_data.get("display_text", "")
            subtitle = slide_data.get("subtitle", "")
            
            prompt = f"""Analyze this TikTok slideshow slide and rate its quality.

Slide Info:
- Type: {slide_type} (hook slides need to be scroll-stopping, content slides need to be readable)
- Main Text: {display_text}
- Subtitle: {subtitle}

Rate each of these criteria from 1-10:
{chr(10).join(f"- {c}" for c in criteria)}

Also provide:
1. Overall score (1-10)
2. Brief feedback (2-3 sentences)
3. Specific suggestions for improvement (list 2-3)
4. Should this slide be regenerated? (yes/no and why)

Respond in JSON format:
{{
    "overall": 8.5,
    "readability": 9,
    "visual_appeal": 8,
    "hook_strength": 8,
    "brand_consistency": 9,
    "feedback": "The text is clear and readable...",
    "suggestions": ["Consider using a bolder font", "..."],
    "should_regenerate": false,
    "regenerate_reason": ""
}}"""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                review_data = json.loads(json_match.group())
            else:
                review_data = {
                    "overall": 7,
                    "feedback": response_text,
                    "suggestions": [],
                    "should_regenerate": False
                }
            
            return {
                "success": True,
                "slide_index": slide_index,
                "image_path": image_path,
                "ratings": {
                    "overall": review_data.get("overall", 7),
                    "readability": review_data.get("readability", 7),
                    "visual_appeal": review_data.get("visual_appeal", 7),
                    "hook_strength": review_data.get("hook_strength", 7),
                    "brand_consistency": review_data.get("brand_consistency", 7)
                },
                "feedback": review_data.get("feedback", ""),
                "suggestions": review_data.get("suggestions", []),
                "should_regenerate": review_data.get("should_regenerate", False),
                "regenerate_reason": review_data.get("regenerate_reason", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def review_all_slides(self) -> Dict[str, Any]:
        """
        Review all slides in the current project and provide aggregate feedback.
        
        Returns:
            {
                "success": True/False,
                "total_slides": 6,
                "average_score": 8.2,
                "slides_to_regenerate": [0, 3],
                "reviews": [...],
                "overall_feedback": "..."
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded."
                }
            
            image_paths = [p for p in self.current_project.get("image_paths", []) if p]
            if not image_paths:
                return {
                    "success": False,
                    "error": "No slides generated yet."
                }
            
            reviews = []
            scores = []
            slides_to_regenerate = []
            
            for i in range(len(image_paths)):
                review = self.review_slide_quality(slide_index=i)
                if review.get("success"):
                    reviews.append(review)
                    scores.append(review.get("ratings", {}).get("overall", 7))
                    if review.get("should_regenerate"):
                        slides_to_regenerate.append(i)
            
            average_score = sum(scores) / len(scores) if scores else 0
            
            return {
                "success": True,
                "total_slides": len(image_paths),
                "average_score": round(average_score, 1),
                "slides_to_regenerate": slides_to_regenerate,
                "reviews": reviews,
                "overall_feedback": f"Reviewed {len(reviews)} slides. Average score: {average_score:.1f}/10. "
                                   f"{len(slides_to_regenerate)} slides recommended for regeneration."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_slides(
        self,
        slide_index: int,
        variations: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate multiple variations of a slide and compare them.
        
        Args:
            slide_index: Which slide to create variations for
            variations: List of variation configs, e.g.:
                        [{"font_name": "bebas"}, {"font_name": "cinzel"}, {"font_name": "cormorant"}]
        
        Returns:
            {
                "success": True/False,
                "variations": [
                    {"config": {...}, "image_path": "...", "score": 8.5},
                    ...
                ],
                "best_variation": 0,
                "recommendation": "The bebas font scored highest..."
            }
        """
        try:
            if not self.current_project:
                return {
                    "success": False,
                    "error": "No project loaded."
                }
            
            slides = self.current_project.get("slides", [])
            if slide_index >= len(slides):
                return {
                    "success": False,
                    "error": f"Slide index {slide_index} out of range."
                }
            
            results = []
            
            for i, variation in enumerate(variations):
                # Generate slide with this variation
                font_name = variation.get("font_name")
                visual_style = variation.get("visual_style", "modern")
                
                # Generate or change font
                if font_name:
                    gen_result = self.change_font_style(
                        slide_index=slide_index,
                        font_name=font_name,
                        visual_style=visual_style
                    )
                else:
                    gen_result = self.generate_single_slide(
                        slide_index=slide_index,
                        visual_style=visual_style
                    )
                
                if gen_result.get("success"):
                    # Review this variation
                    review = self.review_slide_quality(slide_index=slide_index)
                    score = review.get("ratings", {}).get("overall", 7) if review.get("success") else 7
                    
                    results.append({
                        "config": variation,
                        "image_path": gen_result.get("image_path"),
                        "score": score,
                        "feedback": review.get("feedback", "") if review.get("success") else ""
                    })
            
            if not results:
                return {
                    "success": False,
                    "error": "No variations generated successfully."
                }
            
            # Find best variation
            best_idx = max(range(len(results)), key=lambda i: results[i]["score"])
            best = results[best_idx]
            
            # Re-apply best variation
            if best["config"].get("font_name"):
                self.change_font_style(
                    slide_index=slide_index,
                    font_name=best["config"]["font_name"],
                    visual_style=best["config"].get("visual_style", "modern")
                )
            
            return {
                "success": True,
                "variations": results,
                "best_variation": best_idx,
                "recommendation": f"The {best['config']} configuration scored highest at {best['score']}/10."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== LEARNING & MEMORY TOOLS ====================
    
    def store_learning(
        self,
        category: str,
        learning: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a learning/insight for future reference.
        
        The agent can use this to remember what works and what doesn't.
        
        Args:
            category: Category (e.g., "fonts", "hooks", "topics", "performance")
            learning: The insight to store
            context: Optional context data (topic, scores, etc.)
        
        Returns:
            {
                "success": True/False,
                "learning_id": "2024-01-12_001",
                "category": "fonts",
                "learning": "..."
            }
        """
        try:
            learnings_dir = os.path.join("memory", "learnings")
            os.makedirs(learnings_dir, exist_ok=True)
            
            # Load existing learnings
            learnings_file = os.path.join(learnings_dir, f"{category}.json")
            if os.path.exists(learnings_file):
                with open(learnings_file, 'r') as f:
                    learnings = json.load(f)
            else:
                learnings = []
            
            # Create new learning entry
            learning_id = f"{datetime.now().strftime('%Y-%m-%d')}_{len(learnings):03d}"
            entry = {
                "id": learning_id,
                "timestamp": datetime.now().isoformat(),
                "learning": learning,
                "context": context or {},
                "applied_count": 0
            }
            
            learnings.append(entry)
            
            # Save
            with open(learnings_file, 'w') as f:
                json.dump(learnings, f, indent=2)
            
            return {
                "success": True,
                "learning_id": learning_id,
                "category": category,
                "learning": learning
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve stored learnings for a category.
        
        Args:
            category: Category to retrieve (None = all categories)
            limit: Maximum entries to return per category
        
        Returns:
            {
                "success": True/False,
                "learnings": {
                    "fonts": [...],
                    "hooks": [...]
                },
                "total_count": 15
            }
        """
        try:
            learnings_dir = os.path.join("memory", "learnings")
            
            if not os.path.exists(learnings_dir):
                return {
                    "success": True,
                    "learnings": {},
                    "total_count": 0
                }
            
            result = {}
            total = 0
            
            if category:
                # Get specific category
                learnings_file = os.path.join(learnings_dir, f"{category}.json")
                if os.path.exists(learnings_file):
                    with open(learnings_file, 'r') as f:
                        entries = json.load(f)
                    result[category] = entries[-limit:]
                    total = len(entries)
            else:
                # Get all categories
                for filename in os.listdir(learnings_dir):
                    if filename.endswith('.json'):
                        cat = filename[:-5]
                        with open(os.path.join(learnings_dir, filename), 'r') as f:
                            entries = json.load(f)
                        result[cat] = entries[-limit:]
                        total += len(entries)
            
            return {
                "success": True,
                "learnings": result,
                "total_count": total
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_performance_data(
        self,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance data for past projects.
        
        NOTE: TikTok API integration not yet implemented.
        Currently returns mock/stored data.
        
        Args:
            project_id: Specific project to get data for (None = all recent)
        
        Returns:
            {
                "success": True/False,
                "projects": [
                    {
                        "project_id": "...",
                        "title": "...",
                        "views": 1500,
                        "likes": 120,
                        "comments": 15,
                        "shares": 8,
                        "engagement_rate": 0.095
                    }
                ],
                "note": "TikTok API integration pending"
            }
        """
        try:
            performance_file = os.path.join("memory", "performance.json")
            
            if os.path.exists(performance_file):
                with open(performance_file, 'r') as f:
                    data = json.load(f)
            else:
                # Return placeholder structure
                data = {
                    "projects": [],
                    "last_updated": None
                }
            
            projects = data.get("projects", [])
            
            if project_id:
                projects = [p for p in projects if p.get("project_id") == project_id]
            
            return {
                "success": True,
                "projects": projects[-10:],  # Last 10
                "note": "TikTok API integration pending - manually add performance data to memory/performance.json"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def store_performance_data(
        self,
        project_id: str,
        title: str,
        views: int = 0,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store performance data for a project (manual entry until TikTok API).
        
        Args:
            project_id: Unique project identifier
            title: Project title
            views: View count
            likes: Like count
            comments: Comment count
            shares: Share count
            notes: Any notes about performance
        
        Returns:
            {
                "success": True/False,
                "project_id": "...",
                "engagement_rate": 0.095
            }
        """
        try:
            performance_file = os.path.join("memory", "performance.json")
            
            if os.path.exists(performance_file):
                with open(performance_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"projects": [], "last_updated": None}
            
            # Calculate engagement rate
            engagement_rate = (likes + comments + shares) / views if views > 0 else 0
            
            # Create entry
            entry = {
                "project_id": project_id,
                "title": title,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "engagement_rate": round(engagement_rate, 4),
                "notes": notes,
                "recorded_at": datetime.now().isoformat()
            }
            
            # Update or add
            existing_idx = next(
                (i for i, p in enumerate(data["projects"]) if p.get("project_id") == project_id),
                None
            )
            
            if existing_idx is not None:
                data["projects"][existing_idx] = entry
            else:
                data["projects"].append(entry)
            
            data["last_updated"] = datetime.now().isoformat()
            
            # Save
            with open(performance_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return {
                "success": True,
                "project_id": project_id,
                "engagement_rate": entry["engagement_rate"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_best_performing_content(
        self,
        metric: str = "engagement_rate",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get the best performing content based on a metric.
        
        Args:
            metric: Which metric to sort by (views, likes, comments, shares, engagement_rate)
            limit: How many to return
        
        Returns:
            {
                "success": True/False,
                "best_content": [...],
                "insights": "Top performers tend to..."
            }
        """
        try:
            performance_file = os.path.join("memory", "performance.json")
            
            if not os.path.exists(performance_file):
                return {
                    "success": True,
                    "best_content": [],
                    "insights": "No performance data recorded yet."
                }
            
            with open(performance_file, 'r') as f:
                data = json.load(f)
            
            projects = data.get("projects", [])
            
            if not projects:
                return {
                    "success": True,
                    "best_content": [],
                    "insights": "No performance data recorded yet."
                }
            
            # Sort by metric
            sorted_projects = sorted(
                projects,
                key=lambda p: p.get(metric, 0),
                reverse=True
            )[:limit]
            
            # Generate simple insights
            if len(sorted_projects) >= 3:
                avg_engagement = sum(p.get("engagement_rate", 0) for p in sorted_projects[:3]) / 3
                insights = f"Top 3 performers have avg engagement rate of {avg_engagement:.1%}. "
                
                # Look for patterns in titles
                titles = [p.get("title", "") for p in sorted_projects[:3]]
                insights += f"Top titles: {', '.join(titles[:3])}"
            else:
                insights = "Need more data to generate insights."
            
            return {
                "success": True,
                "best_content": sorted_projects,
                "insights": insights
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== UTILITIES ====================
    
    def _safe_filename(self, name: str, max_len: int = 50) -> str:
        """Convert a string to a safe filename."""
        safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe = safe.replace(' ', '_')
        return safe[:max_len]


# Tool definitions for Claude SDK registration
TOOL_DEFINITIONS = [
    {
        "name": "generate_script",
        "description": "Generate a slideshow script from a topic. Creates the content structure for a TikTok slideshow with hook, content slides, and outro.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic for the slideshow (e.g., '5 philosophers who changed the world')"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "generate_single_slide",
        "description": "Generate a single slide (background image + text overlay). Requires generate_script() to be called first.",
        "parameters": {
            "type": "object",
            "properties": {
                "slide_index": {
                    "type": "integer",
                    "description": "Which slide to generate (0-based)"
                },
                "font_name": {
                    "type": "string",
                    "description": "Font to use (e.g., 'bebas', 'cinzel', 'cormorant')"
                },
                "visual_style": {
                    "type": "string",
                    "description": "Style preset: 'modern', 'elegant', or 'philosophaire'"
                },
                "skip_image_generation": {
                    "type": "boolean",
                    "description": "If true, uses solid background (faster for testing)"
                }
            },
            "required": ["slide_index"]
        }
    },
    {
        "name": "generate_all_slides",
        "description": "Generate all slides for the current script.",
        "parameters": {
            "type": "object",
            "properties": {
                "font_name": {
                    "type": "string",
                    "description": "Font to use for all slides"
                },
                "visual_style": {
                    "type": "string",
                    "description": "Style preset"
                },
                "skip_image_generation": {
                    "type": "boolean",
                    "description": "If true, uses solid backgrounds"
                }
            }
        }
    },
    {
        "name": "change_font_style",
        "description": "Re-render a slide with a different font. Uses existing background but re-applies text.",
        "parameters": {
            "type": "object",
            "properties": {
                "slide_index": {
                    "type": "integer",
                    "description": "Which slide to re-render"
                },
                "font_name": {
                    "type": "string",
                    "description": "New font name (e.g., 'bebas', 'cinzel', 'cormorant', 'montserrat')"
                },
                "visual_style": {
                    "type": "string",
                    "description": "Style preset"
                }
            },
            "required": ["slide_index", "font_name"]
        }
    },
    {
        "name": "list_available_fonts",
        "description": "Get list of all available fonts for styling slides.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_video_from_slides",
        "description": "Create a video from generated slides with voiceover audio.",
        "parameters": {
            "type": "object",
            "properties": {
                "audio_text": {
                    "type": "string",
                    "description": "Custom audio text (defaults to script text)"
                },
                "voice_id": {
                    "type": "string",
                    "description": "ElevenLabs voice ID"
                },
                "transition": {
                    "type": "string",
                    "description": "Transition type: 'none', 'crossfade', 'fade_black'"
                },
                "transition_duration": {
                    "type": "number",
                    "description": "Duration of transitions in seconds"
                }
            }
        }
    },
    {
        "name": "send_email_with_content",
        "description": "Send the generated video via email.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body text"
                },
                "caption": {
                    "type": "string",
                    "description": "TikTok caption to include"
                }
            }
        }
    },
    {
        "name": "get_project_state",
        "description": "Get the current project state including script, slides, and paths.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    # ==================== AUTONOMOUS REVIEW TOOLS ====================
    {
        "name": "review_slide_quality",
        "description": "Analyze a generated slide image using vision AI and rate its quality. Returns scores for readability, visual appeal, hook strength, and suggestions for improvement.",
        "parameters": {
            "type": "object",
            "properties": {
                "slide_index": {
                    "type": "integer",
                    "description": "Which slide to review (0-based)"
                },
                "criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of criteria to evaluate"
                }
            },
            "required": ["slide_index"]
        }
    },
    {
        "name": "review_all_slides",
        "description": "Review all slides in the current project and provide aggregate feedback. Returns average scores and identifies slides that should be regenerated.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "compare_slides",
        "description": "Generate multiple variations of a slide (different fonts/styles) and compare them to find the best one.",
        "parameters": {
            "type": "object",
            "properties": {
                "slide_index": {
                    "type": "integer",
                    "description": "Which slide to create variations for"
                },
                "variations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "font_name": {"type": "string"},
                            "visual_style": {"type": "string"}
                        }
                    },
                    "description": "List of variation configs to try"
                }
            },
            "required": ["slide_index", "variations"]
        }
    },
    # ==================== LEARNING & MEMORY TOOLS ====================
    {
        "name": "store_learning",
        "description": "Store a learning/insight for future reference. Use this to remember what works and what doesn't.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category: 'fonts', 'hooks', 'topics', 'styles', 'performance'"
                },
                "learning": {
                    "type": "string",
                    "description": "The insight to store"
                },
                "context": {
                    "type": "object",
                    "description": "Optional context data (topic, scores, etc.)"
                }
            },
            "required": ["category", "learning"]
        }
    },
    {
        "name": "get_learnings",
        "description": "Retrieve stored learnings for a category. Use this before creating content to apply past insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category to retrieve (omit for all)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries to return per category"
                }
            }
        }
    },
    {
        "name": "get_performance_data",
        "description": "Get performance data for past projects (views, likes, engagement). NOTE: TikTok API not yet integrated - data must be manually entered.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Specific project ID (omit for all recent)"
                }
            }
        }
    },
    {
        "name": "store_performance_data",
        "description": "Store performance data for a project (manual entry until TikTok API integration).",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Unique project identifier"
                },
                "title": {
                    "type": "string",
                    "description": "Project title"
                },
                "views": {
                    "type": "integer",
                    "description": "View count"
                },
                "likes": {
                    "type": "integer",
                    "description": "Like count"
                },
                "comments": {
                    "type": "integer",
                    "description": "Comment count"
                },
                "shares": {
                    "type": "integer",
                    "description": "Share count"
                },
                "notes": {
                    "type": "string",
                    "description": "Any notes about performance"
                }
            },
            "required": ["project_id", "title"]
        }
    },
    {
        "name": "get_best_performing_content",
        "description": "Get the best performing content based on a metric. Use this to understand what works.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric to sort by: 'views', 'likes', 'comments', 'shares', 'engagement_rate'"
                },
                "limit": {
                    "type": "integer",
                    "description": "How many to return"
                }
            }
        }
    }
]


if __name__ == "__main__":
    # Test the tools
    print("🧪 Testing AgentTools")
    print("=" * 50)
    
    tools = AgentTools()
    
    # List available fonts
    fonts_result = tools.list_available_fonts()
    print(f"\nAvailable fonts: {fonts_result}")
    
    print("\n✅ AgentTools initialized successfully")
