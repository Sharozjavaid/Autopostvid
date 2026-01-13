"""
Audio-Synced Video Pipeline

This is the main orchestrator for the automated video generation pipeline.
It coordinates all steps to ensure perfect audio-video synchronization.

Pipeline Flow:
1. Generate Script (with word count constraints)
2. Generate Audio (with word-level timestamps)
3. Validate Timing (ensure scenes match clip durations)
4. Generate Images (parallel with audio)
5. Generate Video Clips (fal.ai, sequential)
6. Assemble Final Video (moviepy)
"""

import os
import json
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime

from gemini_handler import GeminiHandler
from voice_generator import VoiceGenerator
from smart_image_generator import SmartImageGenerator
from gpt_image_generator import GPTImageGenerator, check_gpt_image_available
from fal_video_generator import FalVideoGenerator
from timing_calculator import (
    calculate_scene_durations,
    validate_pipeline_timing,
    print_timing_report,
    suggest_script_adjustments,
    validate_and_log
)


class VideoPipeline:
    """
    Automated video generation pipeline with audio synchronization.
    
    Usage:
        pipeline = VideoPipeline()
        result = pipeline.run("5 philosophers who changed the world")
        print(f"Final video: {result['final_video_path']}")
    """
    
    def __init__(
        self,
        target_duration: int = 60,
        clip_duration: int = 6,
        voice_id: str = None,
        output_dir: str = "generated_videos"
    ):
        """
        Initialize the pipeline.
        
        Args:
            target_duration: Target video duration in seconds (default 60)
            clip_duration: Duration per clip in seconds (5 or 6, default 6)
            voice_id: ElevenLabs voice ID (optional, uses default if not provided)
            output_dir: Output directory for final videos
        """
        self.target_duration = target_duration
        self.clip_duration = clip_duration
        self.voice_id = voice_id
        self.output_dir = output_dir
        
        # Ensure output directories exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs("generated_scripts", exist_ok=True)
        os.makedirs("generated_audio", exist_ok=True)
        os.makedirs("generated_images", exist_ok=True)
        os.makedirs(f"{output_dir}/clips", exist_ok=True)
        
        # Initialize components
        self.gemini = GeminiHandler()
        self.voice = VoiceGenerator()
        self.image_gen = SmartImageGenerator()
        
        # GPT Image 1.5 generator (initialized lazily)
        self._gpt_image_gen = None
        
        # fal.ai video generator (initialized lazily)
        self._fal_gen = None
        
        # Callback for progress updates
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
    
    @property
    def fal_gen(self) -> FalVideoGenerator:
        """Lazy initialization of fal.ai video generator."""
        if self._fal_gen is None:
            self._fal_gen = FalVideoGenerator()
        return self._fal_gen
    
    @property
    def gpt_image_gen(self) -> GPTImageGenerator:
        """Lazy initialization of GPT Image 1.5 generator."""
        if self._gpt_image_gen is None:
            self._gpt_image_gen = GPTImageGenerator(quality="low")
        return self._gpt_image_gen
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Set callback for progress updates. Callback receives (stage, current, total)."""
        self.progress_callback = callback
    
    def _notify_progress(self, stage: str, current: int = 0, total: int = 0):
        """Notify progress callback if set."""
        if self.progress_callback:
            self.progress_callback(stage, current, total)
        print(f"[{stage}] {current}/{total}" if total else f"[{stage}]")
    
    def run(
        self,
        topic: str,
        skip_video_clips: bool = False,
        image_model: str = "gpt15"
    ) -> Dict:
        """
        Run the complete video generation pipeline.
        
        Args:
            topic: The video topic (e.g., "5 philosophers who changed the world")
            skip_video_clips: If True, skip fal.ai video generation (for testing)
            image_model: Image model to use:
                - "gpt15" (default) - GPT Image 1.5 via fal.ai with bold text overlays (RECOMMENDED)
                - "nano" - Gemini 3 Pro Image
                - "openai" - OpenAI DALL-E 3
            
        Returns:
            {
                "success": bool,
                "topic": str,
                "script_path": str,
                "audio_path": str,
                "image_paths": [str],
                "video_clip_paths": [str],
                "final_video_path": str,
                "timing_report": dict,
                "duration": float,
                "error": str (if failed)
            }
        """
        start_time = time.time()
        result = {
            "success": False,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # =====================
            # STEP 1: Generate Script
            # =====================
            self._notify_progress("SCRIPT_GENERATION")
            
            script_data = self.gemini.generate_timed_script(
                topic=topic,
                target_duration=self.target_duration,
                clip_duration=self.clip_duration
            )
            
            if not script_data:
                raise Exception("Failed to generate script")
            
            # Add title if missing
            if 'title' not in script_data:
                script_data['title'] = topic
            
            # Save script
            safe_title = self._safe_filename(script_data.get('title', topic))
            script_path = f"generated_scripts/{safe_title}.json"
            with open(script_path, 'w') as f:
                json.dump(script_data, f, indent=2)
            
            result['script_path'] = script_path
            result['script_data'] = script_data
            
            scenes = script_data.get('scenes', [])
            print(f"✅ Script generated: {len(scenes)} scenes")
            
            # =====================
            # STEP 2: Generate Audio with Timestamps
            # =====================
            self._notify_progress("AUDIO_GENERATION")
            
            full_script = script_data.get('script', '')
            audio_filename = f"{safe_title}_synced.mp3"
            
            audio_result = self.voice.generate_voiceover_with_timestamps(
                script=full_script,
                scenes=scenes,
                voice_id=self.voice_id,
                filename=audio_filename
            )
            
            if not audio_result:
                raise Exception("Failed to generate audio with timestamps")
            
            result['audio_path'] = audio_result['audio_path']
            result['audio_duration'] = audio_result['total_duration']
            
            print(f"✅ Audio generated: {audio_result['total_duration']:.2f}s")
            
            # =====================
            # STEP 3: Validate Timing
            # =====================
            self._notify_progress("TIMING_VALIDATION")
            
            scene_timings = audio_result.get('scene_timings', [])
            
            # Use the comprehensive validate_and_log function
            enhanced_scenes, timing_report, is_valid = validate_and_log(
                topic=topic,
                scenes=scenes,
                scene_timings=scene_timings,
                audio_path=audio_result['audio_path']
            )
            
            result['timing_report'] = timing_report
            result['enhanced_scenes'] = enhanced_scenes
            
            if not is_valid:
                print("⚠️ Warning: Timing validation failed, but continuing...")
                suggestions = suggest_script_adjustments(enhanced_scenes)
                if suggestions:
                    print("Suggested adjustments:")
                    for s in suggestions:
                        print(f"  Scene {s['scene_number']}: {s['action']}")
            
            # =====================
            # STEP 4: Generate Images (with themed text overlays)
            # =====================
            self._notify_progress("IMAGE_GENERATION", 0, len(scenes))
            
            # Get list_items for person names
            list_items = script_data.get('list_items', [])
            
            image_paths = []
            
            # Determine which image generator to use
            use_gpt15 = image_model == "gpt15" and check_gpt_image_available()
            
            if use_gpt15:
                print(f"🎨 Using GPT Image 1.5 via fal.ai (with bold text overlays)")
            elif image_model == "gpt15":
                print(f"⚠️ GPT Image 1.5 requested but FAL_KEY not set, falling back to nano")
                image_model = "nano"
            
            for i, scene in enumerate(scenes):
                self._notify_progress("IMAGE_GENERATION", i + 1, len(scenes))
                
                scene_num = scene.get('scene_number', i + 1)
                visual_desc = scene.get('visual_description', '')
                
                # Enrich scene with person name from list_items
                enriched_scene = {**scene}
                list_item_num = scene.get('list_item', 0)
                if list_item_num and list_items:
                    matching_item = next((item for item in list_items if item.get('number') == list_item_num), None)
                    if matching_item:
                        enriched_scene['person_name'] = matching_item.get('name', '')
                
                try:
                    if use_gpt15:
                        # GPT Image 1.5 - best for bold text overlays
                        image_path = self.gpt_image_gen.generate_philosophy_image(
                            scene_data=enriched_scene,
                            story_title=script_data.get('title', topic),
                            story_data=script_data
                        )
                    elif image_model == "nano":
                        # Gemini 3 Pro Image (Nano)
                        image_path = self.image_gen.generate_image_with_nano(
                            prompt=visual_desc,
                            scene_number=scene_num,
                            story_title=script_data.get('title', topic),
                            scene_data=enriched_scene
                        )
                    else:
                        # Fallback to nano
                        image_path = self.image_gen.generate_image_with_nano(
                            prompt=visual_desc,
                            scene_number=scene_num,
                            story_title=script_data.get('title', topic),
                            scene_data=enriched_scene
                        )
                    
                    if image_path and os.path.exists(image_path):
                        image_paths.append(image_path)
                    else:
                        print(f"⚠️ Failed to generate image for scene {scene_num}")
                except Exception as e:
                    print(f"⚠️ Error generating image for scene {scene_num}: {e}")
            
            result['image_paths'] = image_paths
            print(f"✅ Generated {len(image_paths)}/{len(scenes)} images")
            
            if len(image_paths) < 2:
                raise Exception("Not enough images generated for video")
            
            # =====================
            # STEP 5: Generate Video Clips (fal.ai)
            # =====================
            if skip_video_clips:
                print("⏭️ Skipping video clip generation (skip_video_clips=True)")
                result['video_clip_paths'] = []
            else:
                self._notify_progress("VIDEO_CLIP_GENERATION", 0, len(image_paths) - 1)
                
                # Get clip durations for each scene
                clip_durations = []
                for scene in enhanced_scenes:
                    clip_dur = scene.get('clip_duration', self.clip_duration)
                    clip_durations.append(str(clip_dur))
                
                # Generate transition videos
                video_clip_paths = []
                scene_descriptions = [s.get('visual_description', '') for s in scenes]
                
                try:
                    # Upload all images first
                    uploaded_urls = []
                    for img_path in image_paths:
                        url = self.fal_gen.upload_image(img_path)
                        uploaded_urls.append(url)
                    
                    # Generate transitions
                    num_transitions = len(image_paths) - 1
                    for i in range(num_transitions):
                        self._notify_progress("VIDEO_CLIP_GENERATION", i + 1, num_transitions)
                        
                        # Use scene-specific duration if available
                        duration = clip_durations[i] if i < len(clip_durations) else str(self.clip_duration)
                        
                        scene_desc = scene_descriptions[i] if i < len(scene_descriptions) else ""
                        prompt = self.fal_gen.TRANSITION_PROMPT_TEMPLATE.format(
                            scene_description=scene_desc
                        )
                        
                        video_path = self.fal_gen.generate_transition_video(
                            start_image_url=uploaded_urls[i],
                            end_image_url=uploaded_urls[i + 1],
                            prompt=prompt,
                            scene_number=i + 1,
                            story_title=safe_title,
                            duration=duration
                        )
                        
                        if video_path:
                            video_clip_paths.append(video_path)
                    
                    result['video_clip_paths'] = video_clip_paths
                    print(f"✅ Generated {len(video_clip_paths)}/{num_transitions} video clips")
                    
                except Exception as e:
                    print(f"⚠️ Error generating video clips: {e}")
                    result['video_clip_paths'] = []
            
            # =====================
            # STEP 6: Assemble Final Video
            # =====================
            if result.get('video_clip_paths'):
                self._notify_progress("FINAL_ASSEMBLY")
                
                final_video_path = self.fal_gen.create_final_video_with_audio(
                    video_paths=result['video_clip_paths'],
                    audio_path=result['audio_path'],
                    story_title=safe_title,
                    crossfade_duration=0.5
                )
                
                if final_video_path and os.path.exists(final_video_path):
                    result['final_video_path'] = final_video_path
                    print(f"✅ Final video: {final_video_path}")
                else:
                    print("⚠️ Failed to create final video")
            else:
                print("⏭️ Skipping final assembly (no video clips)")
            
            # =====================
            # COMPLETE
            # =====================
            result['success'] = True
            result['duration'] = time.time() - start_time
            
            self._notify_progress("COMPLETE")
            print(f"\n🎉 Pipeline complete in {result['duration']:.1f}s")
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['duration'] = time.time() - start_time
            print(f"\n❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def run_batch(
        self,
        topics: List[str],
        delay_between: int = 5
    ) -> List[Dict]:
        """
        Run pipeline for multiple topics.
        
        Args:
            topics: List of topics to process
            delay_between: Seconds to wait between topics
            
        Returns:
            List of result dicts for each topic
        """
        results = []
        
        for i, topic in enumerate(topics):
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(topics)}: {topic}")
            print('='*60)
            
            result = self.run(topic)
            results.append(result)
            
            if i < len(topics) - 1:
                print(f"Waiting {delay_between}s before next topic...")
                time.sleep(delay_between)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'='*60}")
        print(f"BATCH COMPLETE: {successful}/{len(topics)} successful")
        print('='*60)
        
        return results
    
    def _safe_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        return "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')


# Convenience function for quick runs
def generate_video(
    topic: str,
    target_duration: int = 60,
    clip_duration: int = 6,
    voice_id: str = None,
    image_model: str = "gpt15"
) -> Dict:
    """
    Quick function to generate a video from a topic.
    
    Args:
        topic: The video topic
        target_duration: Target video duration in seconds
        clip_duration: Duration per clip (5 or 6)
        voice_id: Optional ElevenLabs voice ID
        image_model: Image model - "gpt15" (default, recommended), "nano", or "openai"
        
    Returns:
        Pipeline result dict
    """
    pipeline = VideoPipeline(
        target_duration=target_duration,
        clip_duration=clip_duration,
        voice_id=voice_id
    )
    return pipeline.run(topic, image_model=image_model)


# Example usage
if __name__ == "__main__":
    import sys
    
    # Default topic or from command line
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "5 philosophers who changed the world"
    
    print(f"🎬 Generating video for: {topic}")
    print("="*60)
    
    result = generate_video(
        topic=topic,
        target_duration=60,
        clip_duration=6
    )
    
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Script: {result.get('script_path')}")
        print(f"   Audio: {result.get('audio_path')}")
        print(f"   Images: {len(result.get('image_paths', []))}")
        print(f"   Video Clips: {len(result.get('video_clip_paths', []))}")
        print(f"   Final Video: {result.get('final_video_path')}")
        print(f"   Duration: {result.get('duration', 0):.1f}s")
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
