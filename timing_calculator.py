"""
Timing Calculator for Audio-Synced Video Pipeline

Calculates scene durations from audio timestamps and determines
optimal video clip durations (5s or 6s) for each scene.

Also provides validation and logging for timing issues.
"""

from typing import List, Dict, Tuple, Optional
import math
import logging
import os
from datetime import datetime

# Set up logging for timing validation
TIMING_LOG_FILE = "timing_validation.log"

def get_timing_logger() -> logging.Logger:
    """Get or create a logger for timing validation."""
    logger = logging.getLogger('timing_validator')
    
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(TIMING_LOG_FILE)
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)  # Only warnings and above to console
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger


# Configuration
DEFAULT_WORDS_PER_SECOND = 2.5  # Average narration speed
VALID_CLIP_DURATIONS = [5, 6]   # fal.ai supported durations
MAX_TIMING_VARIANCE = 0.5       # Acceptable seconds over/under per scene


def calculate_scene_durations(
    scenes: List[Dict], 
    scene_timings: List[Dict]
) -> List[Dict]:
    """
    Enhance scenes with timing information and optimal clip durations.
    
    Args:
        scenes: Original scene list from script generation
        scene_timings: Timing data from audio generation with timestamps
        
    Returns:
        Enhanced scenes with:
        - audio_start: when this scene's narration starts
        - audio_end: when this scene's narration ends
        - audio_duration: exact duration in seconds
        - clip_duration: 5 or 6 (optimal fal.ai clip length)
        - timing_variance: how far off from ideal
    """
    enhanced_scenes = []
    
    for scene in scenes:
        scene_num = scene.get('scene_number', len(enhanced_scenes) + 1)
        
        # Find matching timing data
        timing = None
        for t in scene_timings:
            if t.get('scene_number') == scene_num:
                timing = t
                break
        
        # Create enhanced scene copy
        enhanced = scene.copy()
        
        if timing:
            audio_duration = timing['duration']
            
            # Choose optimal clip duration (5 or 6 seconds)
            clip_duration = choose_clip_duration(audio_duration)
            
            enhanced.update({
                'audio_start': timing['start'],
                'audio_end': timing['end'],
                'audio_duration': audio_duration,
                'clip_duration': clip_duration,
                'timing_variance': round(audio_duration - clip_duration, 2),
                'timing_status': get_timing_status(audio_duration, clip_duration)
            })
        else:
            # Estimate from word count if no timing available
            text = scene.get('text', '')
            word_count = len(text.split())
            estimated_duration = word_count / DEFAULT_WORDS_PER_SECOND
            clip_duration = choose_clip_duration(estimated_duration)
            
            enhanced.update({
                'audio_duration': round(estimated_duration, 2),
                'clip_duration': clip_duration,
                'timing_variance': round(estimated_duration - clip_duration, 2),
                'timing_status': 'estimated',
                'estimated': True
            })
        
        enhanced_scenes.append(enhanced)
    
    return enhanced_scenes


def choose_clip_duration(audio_duration: float) -> int:
    """
    Choose the best clip duration (5 or 6 seconds) for a given audio duration.
    
    Strategy: Choose the clip duration that results in the smallest 
    absolute variance, with a slight preference for 6s if equal.
    """
    if audio_duration <= 0:
        return 5
    
    # Calculate variance for each option
    var_5 = abs(audio_duration - 5)
    var_6 = abs(audio_duration - 6)
    
    # If audio is very short, use 5s
    if audio_duration < 4:
        return 5
    
    # If audio is long, use 6s
    if audio_duration > 6.5:
        return 6
    
    # Choose the one with less variance
    if var_5 < var_6:
        return 5
    else:
        return 6


def get_timing_status(audio_duration: float, clip_duration: int) -> str:
    """Categorize the timing match quality."""
    variance = abs(audio_duration - clip_duration)
    
    if variance <= 0.3:
        return 'perfect'
    elif variance <= MAX_TIMING_VARIANCE:
        return 'good'
    elif variance <= 1.0:
        return 'acceptable'
    else:
        return 'warning'


def validate_pipeline_timing(enhanced_scenes: List[Dict]) -> Dict:
    """
    Validate the overall timing of the pipeline and provide a report.
    
    Returns:
        {
            "total_audio_duration": float,
            "total_clip_duration": float,
            "overall_variance": float,
            "scene_count": int,
            "warnings": [str],
            "is_valid": bool,
            "scenes_by_status": {...},
            "speed_adjustment": float,  # How much video needs to be sped/slowed
            "adjustment_quality": str   # "perfect", "good", "acceptable", "poor"
        }
    """
    total_audio = sum(s.get('audio_duration', 0) for s in enhanced_scenes)
    total_clip = sum(s.get('clip_duration', 6) for s in enhanced_scenes)
    
    warnings = []
    status_counts = {'perfect': 0, 'good': 0, 'acceptable': 0, 'warning': 0, 'estimated': 0}
    
    for scene in enhanced_scenes:
        status = scene.get('timing_status', 'unknown')
        if status in status_counts:
            status_counts[status] += 1
        
        if status == 'warning':
            scene_num = scene.get('scene_number', '?')
            variance = scene.get('timing_variance', 0)
            warnings.append(
                f"Scene {scene_num}: Audio {scene.get('audio_duration', 0):.1f}s vs "
                f"Clip {scene.get('clip_duration', 0)}s (variance: {variance:+.1f}s)"
            )
    
    overall_variance = total_audio - total_clip
    is_valid = abs(overall_variance) < (len(enhanced_scenes) * MAX_TIMING_VARIANCE)
    
    # Calculate speed adjustment needed
    if total_clip > 0 and total_audio > 0:
        speed_factor = total_clip / total_audio
        speed_adjustment_pct = abs(1 - speed_factor) * 100
        
        if speed_adjustment_pct <= 5:
            adjustment_quality = "perfect"
        elif speed_adjustment_pct <= 10:
            adjustment_quality = "good"
        elif speed_adjustment_pct <= 20:
            adjustment_quality = "acceptable"
        else:
            adjustment_quality = "poor"
        
        # Direction of adjustment
        if total_audio > total_clip:
            adjustment_direction = "slow_down"
            adjustment_note = f"Video will be slowed by {speed_adjustment_pct:.1f}%"
        else:
            adjustment_direction = "speed_up"
            adjustment_note = f"Video will be sped up by {speed_adjustment_pct:.1f}%"
    else:
        speed_adjustment_pct = 0
        adjustment_quality = "unknown"
        adjustment_direction = "none"
        adjustment_note = "Unable to calculate"
    
    return {
        "total_audio_duration": round(total_audio, 2),
        "total_clip_duration": total_clip,
        "overall_variance": round(overall_variance, 2),
        "scene_count": len(enhanced_scenes),
        "warnings": warnings,
        "is_valid": is_valid,
        "scenes_by_status": status_counts,
        "speed_adjustment_pct": round(speed_adjustment_pct, 1),
        "adjustment_direction": adjustment_direction,
        "adjustment_quality": adjustment_quality,
        "adjustment_note": adjustment_note
    }


def suggest_script_adjustments(enhanced_scenes: List[Dict]) -> List[Dict]:
    """
    Suggest word count adjustments for scenes that don't fit well.
    
    Returns list of suggestions for scenes that need adjustment.
    """
    suggestions = []
    
    for scene in enhanced_scenes:
        status = scene.get('timing_status', '')
        
        if status in ['warning', 'acceptable'] and scene.get('timing_variance', 0) != 0:
            scene_num = scene.get('scene_number', '?')
            current_words = len(scene.get('text', '').split())
            audio_duration = scene.get('audio_duration', 0)
            clip_duration = scene.get('clip_duration', 6)
            variance = scene.get('timing_variance', 0)
            
            if variance > 0:
                # Audio is longer than clip - need fewer words
                target_words = int(clip_duration * DEFAULT_WORDS_PER_SECOND)
                words_to_remove = current_words - target_words
                suggestions.append({
                    "scene_number": scene_num,
                    "issue": "too_long",
                    "current_words": current_words,
                    "target_words": target_words,
                    "action": f"Remove ~{words_to_remove} words",
                    "variance": variance
                })
            else:
                # Audio is shorter than clip - could add words (or it's fine)
                if abs(variance) > 1.0:
                    target_words = int(clip_duration * DEFAULT_WORDS_PER_SECOND)
                    words_to_add = target_words - current_words
                    suggestions.append({
                        "scene_number": scene_num,
                        "issue": "too_short",
                        "current_words": current_words,
                        "target_words": target_words,
                        "action": f"Add ~{words_to_add} words",
                        "variance": variance
                    })
    
    return suggestions


def estimate_scene_duration_from_text(text: str, words_per_second: float = None) -> float:
    """Estimate how long a piece of text will take to narrate."""
    wps = words_per_second or DEFAULT_WORDS_PER_SECOND
    word_count = len(text.split())
    return word_count / wps


def calculate_target_word_count(target_duration: float, words_per_second: float = None) -> int:
    """Calculate target word count for a given duration."""
    wps = words_per_second or DEFAULT_WORDS_PER_SECOND
    return int(target_duration * wps)


def get_optimal_scene_word_counts(
    num_scenes: int, 
    target_total_duration: float = 60,
    clip_duration: int = 6
) -> List[Dict]:
    """
    Calculate optimal word counts for each scene given constraints.
    
    Args:
        num_scenes: Number of scenes to generate
        target_total_duration: Target total video duration in seconds
        clip_duration: Duration per clip (5 or 6)
        
    Returns:
        List of dicts with scene_number and target_word_count
    """
    words_per_scene = calculate_target_word_count(clip_duration)
    
    return [
        {
            "scene_number": i + 1,
            "target_word_count": words_per_scene,
            "target_duration": clip_duration,
            "word_range": (words_per_scene - 2, words_per_scene + 2)
        }
        for i in range(num_scenes)
    ]


def print_timing_report(enhanced_scenes: List[Dict], validation: Dict) -> None:
    """Print a formatted timing report to console."""
    print("\n" + "=" * 60)
    print("TIMING VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nTotal Scenes: {validation['scene_count']}")
    print(f"Total Audio Duration: {validation['total_audio_duration']:.2f}s")
    print(f"Total Clip Duration: {validation['total_clip_duration']}s")
    print(f"Overall Variance: {validation['overall_variance']:+.2f}s")
    print(f"Pipeline Valid: {'✅ Yes' if validation['is_valid'] else '❌ No'}")
    
    print("\nScene Status Breakdown:")
    for status, count in validation['scenes_by_status'].items():
        if count > 0:
            emoji = {'perfect': '🎯', 'good': '✅', 'acceptable': '⚠️', 'warning': '❌', 'estimated': '📊'}.get(status, '?')
            print(f"  {emoji} {status.capitalize()}: {count}")
    
    if validation['warnings']:
        print("\n⚠️ Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("\nScene Details:")
    print("-" * 60)
    for scene in enhanced_scenes:
        scene_num = scene.get('scene_number', '?')
        audio_dur = scene.get('audio_duration', 0)
        clip_dur = scene.get('clip_duration', 0)
        status = scene.get('timing_status', 'unknown')
        variance = scene.get('timing_variance', 0)
        
        status_emoji = {'perfect': '🎯', 'good': '✅', 'acceptable': '⚠️', 'warning': '❌', 'estimated': '📊'}.get(status, '?')
        
        print(f"  Scene {scene_num:2d}: Audio {audio_dur:5.2f}s → Clip {clip_dur}s "
              f"({variance:+.2f}s) {status_emoji}")
    
    print("=" * 60 + "\n")


def log_timing_validation(
    topic: str,
    enhanced_scenes: List[Dict],
    validation: Dict,
    audio_path: str = None
) -> None:
    """
    Log detailed timing validation to file for debugging and analysis.
    
    This creates a permanent record of timing issues that can be reviewed
    to improve the pipeline over time.
    """
    logger = get_timing_logger()
    
    # Log header
    logger.info("=" * 60)
    logger.info(f"TIMING VALIDATION: {topic}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if audio_path:
        logger.info(f"Audio: {audio_path}")
    logger.info("=" * 60)
    
    # Summary
    logger.info(f"Scenes: {validation['scene_count']}")
    logger.info(f"Audio Duration: {validation['total_audio_duration']:.2f}s")
    logger.info(f"Clip Duration: {validation['total_clip_duration']}s")
    logger.info(f"Variance: {validation['overall_variance']:+.2f}s")
    logger.info(f"Valid: {validation['is_valid']}")
    
    # Status breakdown
    for status, count in validation['scenes_by_status'].items():
        if count > 0:
            logger.info(f"  {status}: {count}")
    
    # Log warnings at WARNING level
    for warning in validation.get('warnings', []):
        logger.warning(warning)
    
    # Log scene details at DEBUG level
    for scene in enhanced_scenes:
        scene_num = scene.get('scene_number', '?')
        audio_dur = scene.get('audio_duration', 0)
        clip_dur = scene.get('clip_duration', 0)
        status = scene.get('timing_status', 'unknown')
        variance = scene.get('timing_variance', 0)
        word_count = len(scene.get('text', '').split())
        
        if status == 'warning':
            logger.warning(
                f"Scene {scene_num}: {word_count} words, "
                f"audio={audio_dur:.2f}s, clip={clip_dur}s, "
                f"variance={variance:+.2f}s"
            )
        else:
            logger.debug(
                f"Scene {scene_num}: {word_count} words, "
                f"audio={audio_dur:.2f}s, clip={clip_dur}s, "
                f"variance={variance:+.2f}s, status={status}"
            )
    
    # If validation failed, log error
    if not validation['is_valid']:
        logger.error(
            f"Pipeline timing validation FAILED for '{topic}'. "
            f"Overall variance: {validation['overall_variance']:+.2f}s"
        )
    
    logger.info("-" * 60)


def validate_and_log(
    topic: str,
    scenes: List[Dict],
    scene_timings: List[Dict],
    audio_path: str = None
) -> Tuple[List[Dict], Dict, bool]:
    """
    Complete validation workflow: calculate, validate, log, and report.
    
    This is the main entry point for timing validation in the pipeline.
    
    Args:
        topic: Video topic (for logging)
        scenes: Original scene list from script
        scene_timings: Timing data from audio generation
        audio_path: Path to audio file (for logging)
        
    Returns:
        Tuple of (enhanced_scenes, validation_dict, is_valid)
    """
    # Calculate scene durations
    enhanced_scenes = calculate_scene_durations(scenes, scene_timings)
    
    # Validate pipeline timing
    validation = validate_pipeline_timing(enhanced_scenes)
    
    # Log to file
    log_timing_validation(topic, enhanced_scenes, validation, audio_path)
    
    # Print report to console
    print_timing_report(enhanced_scenes, validation)
    
    return enhanced_scenes, validation, validation['is_valid']


# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_scenes = [
        {"scene_number": 1, "text": "These five philosophers literally invented how modern humans think."},
        {"scene_number": 2, "text": "Number one: Socrates. The godfather of questions. He taught us to question everything."},
        {"scene_number": 3, "text": "His warning? The unexamined life is not worth living."},
    ]
    
    sample_timings = [
        {"scene_number": 1, "start": 0.0, "end": 4.2, "duration": 4.2},
        {"scene_number": 2, "start": 4.2, "end": 10.5, "duration": 6.3},
        {"scene_number": 3, "start": 10.5, "end": 14.8, "duration": 4.3},
    ]
    
    enhanced = calculate_scene_durations(sample_scenes, sample_timings)
    validation = validate_pipeline_timing(enhanced)
    print_timing_report(enhanced, validation)
    
    suggestions = suggest_script_adjustments(enhanced)
    if suggestions:
        print("Suggested Adjustments:")
        for s in suggestions:
            print(f"  Scene {s['scene_number']}: {s['action']}")
