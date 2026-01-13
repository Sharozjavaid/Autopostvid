"""
Resume generating transitions from where the process left off.
This script picks up from transition 8 and continues to the end.
"""

import os
import glob
from fal_video_generator import FalVideoGenerator
import json

def resume_transitions():
    """Resume transition generation from the last completed clip."""
    
    story_title = "5_reasons_why_philosophy_could_save_modern_day_brain_rotted_kids"
    
    # Load the script for scene descriptions
    script_path = f"generated_scripts/{story_title}.json"
    with open(script_path, 'r') as f:
        script_data = json.load(f)
    
    scenes = script_data.get('scenes', [])
    
    # Find all images for this story (sorted by scene number)
    image_pattern = f"generated_images/{story_title}_scene_*_gpt15.png"
    image_files = sorted(glob.glob(image_pattern), 
                         key=lambda x: int(x.split('_scene_')[1].split('_')[0]))
    
    print(f"Found {len(image_files)} images:")
    for img in image_files:
        print(f"  - {img}")
    
    # Find existing transition clips
    clips_pattern = f"generated_videos/clips/{story_title}_transition_*.mp4"
    existing_clips = sorted(glob.glob(clips_pattern),
                           key=lambda x: int(x.split('_transition_')[1].split('.')[0]))
    
    print(f"\nFound {len(existing_clips)} existing transition clips:")
    for clip in existing_clips:
        print(f"  - {clip}")
    
    # Determine which transitions are missing
    num_images = len(image_files)
    total_transitions_needed = num_images - 1
    
    # Get the last completed transition number
    completed_transition_numbers = [
        int(c.split('_transition_')[1].split('.')[0]) for c in existing_clips
    ]
    
    if completed_transition_numbers:
        last_completed = max(completed_transition_numbers)
    else:
        last_completed = 0
    
    print(f"\nTotal transitions needed: {total_transitions_needed}")
    print(f"Last completed transition: {last_completed}")
    
    # Find missing transitions
    missing = []
    for i in range(1, total_transitions_needed + 1):
        if i not in completed_transition_numbers:
            missing.append(i)
    
    if not missing:
        print("\n✅ All transitions are complete! Nothing to resume.")
        return existing_clips
    
    print(f"Missing transitions: {missing}")
    
    # Initialize generator
    gen = FalVideoGenerator()
    
    # Generate missing transitions
    new_clips = []
    for transition_num in missing:
        # Transition N uses image N and image N+1
        start_idx = transition_num - 1  # 0-indexed
        end_idx = transition_num  # 0-indexed
        
        if end_idx >= len(image_files):
            print(f"⚠️ Not enough images for transition {transition_num}")
            continue
        
        start_image = image_files[start_idx]
        end_image = image_files[end_idx]
        
        print(f"\n🎬 Resuming transition {transition_num}: Image {transition_num} → Image {transition_num + 1}")
        print(f"   Start: {start_image}")
        print(f"   End: {end_image}")
        
        # Get scene description
        if transition_num <= len(scenes):
            scene_desc = scenes[transition_num - 1].get('visual_description', f'Scene {transition_num}')
            raw_duration = scenes[transition_num - 1].get('target_duration', 6)
            # fal.ai only accepts '6' or '10' - round to nearest valid value
            duration = "6" if float(raw_duration) <= 8 else "10"
        else:
            scene_desc = f"Scene {transition_num}"
            duration = "6"
        
        # Upload images
        print(f"\n📤 Uploading images for transition {transition_num}...")
        start_url = gen.upload_image(start_image)
        end_url = gen.upload_image(end_image)
        
        # Build prompt
        prompt = gen.TRANSITION_PROMPT_TEMPLATE.format(scene_description=scene_desc)
        
        # Generate transition
        video_path = gen.generate_transition_video(
            start_image_url=start_url,
            end_image_url=end_url,
            prompt=prompt,
            scene_number=transition_num,
            story_title=story_title,
            duration=duration
        )
        
        if video_path:
            new_clips.append(video_path)
            print(f"✅ Transition {transition_num} complete!")
        else:
            print(f"❌ Failed to generate transition {transition_num}")
    
    # Return all clips (existing + new)
    all_clips = sorted(
        glob.glob(clips_pattern),
        key=lambda x: int(x.split('_transition_')[1].split('.')[0])
    )
    
    print(f"\n🎉 Resume complete!")
    print(f"   Generated: {len(new_clips)} new transitions")
    print(f"   Total clips: {len(all_clips)}/{total_transitions_needed}")
    
    if len(all_clips) == total_transitions_needed:
        print("\n✅ All transitions are now complete! Ready for final video assembly.")
    
    return all_clips


if __name__ == "__main__":
    clips = resume_transitions()
    print(f"\nAll clips: {clips}")
