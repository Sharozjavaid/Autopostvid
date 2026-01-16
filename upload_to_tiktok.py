#!/usr/bin/env python3
"""
TikTok Slideshow Uploader

Two modes:
1. Video slideshow - combines images into a video (works with local files)
2. Photo slideshow - each image is a swipeable slide (native TikTok carousel)

Usage:
    # Video slideshow (default)
    python upload_to_tiktok.py --slides "folder/slide_*.png" --caption "#SlideFilm"
    
    # Photo slideshow (native swipeable carousel) 
    python upload_to_tiktok.py --slides "folder/slide_*.png" --mode photo --caption "#SlideFilm"
"""

import argparse
import subprocess
import os
import json
import glob
import requests
from pathlib import Path

# API base URL for image hosting
API_BASE_URL = "https://api.cofndrly.com"


def create_video_from_slides(slide_paths, output_path, duration_per_slide=5):
    """Create a video from slide images using ffmpeg."""
    
    # Create concat file
    concat_file = "/tmp/tiktok_slides_concat.txt"
    with open(concat_file, 'w') as f:
        for slide in slide_paths:
            f.write(f"file '{os.path.abspath(slide)}'\n")
            f.write(f"duration {duration_per_slide}\n")
        # Add last slide again for ffmpeg
        f.write(f"file '{os.path.abspath(slide_paths[-1])}'\n")
    
    total_duration = len(slide_paths) * duration_per_slide
    
    # Run ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(total_duration),
        output_path
    ]
    
    print(f"🎬 Creating video from {len(slide_paths)} slides...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Video created: {output_path}")
        return True
    else:
        print(f"❌ Error creating video: {result.stderr}")
        return False


def upload_images_to_server(slide_paths, convert_to_jpeg=True):
    """Copy images to server and return public URLs.
    
    TikTok only supports JPEG and WebP for photo posts (not PNG).
    If convert_to_jpeg=True, PNG files are converted to JPEG first.
    """
    print("📤 Uploading images to server...")
    
    if convert_to_jpeg:
        print("   (Converting to JPEG for TikTok compatibility)")
    
    image_urls = []
    for slide_path in slide_paths:
        original_filename = Path(slide_path).name
        
        # Convert PNG to JPEG if needed (TikTok doesn't support PNG)
        if convert_to_jpeg and slide_path.lower().endswith('.png'):
            from PIL import Image
            
            # Convert to JPEG
            jpeg_filename = original_filename.rsplit('.', 1)[0] + '.jpg'
            jpeg_path = f"/tmp/{jpeg_filename}"
            
            img = Image.open(slide_path)
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(jpeg_path, 'JPEG', quality=95)
            
            upload_path = jpeg_path
            final_filename = jpeg_filename
        else:
            upload_path = slide_path
            final_filename = original_filename
        
        # Copy to /tmp on VM first (no permission issues)
        scp_cmd = [
            "gcloud", "compute", "scp",
            upload_path,
            f"philosophy-bot-vm:/tmp/{final_filename}",
            "--zone=us-central1-a"
        ]
        result = subprocess.run(scp_cmd, capture_output=True)
        
        if result.returncode == 0:
            # Move to generated_images with sudo
            move_cmd = [
                "gcloud", "compute", "ssh",
                "philosophy-bot-vm",
                "--zone=us-central1-a",
                "--command",
                f"sudo mv /tmp/{final_filename} /home/runner/philosophy_video_generator/generated_images/"
            ]
            subprocess.run(move_cmd, capture_output=True)
            
            url = f"{API_BASE_URL}/static/images/{final_filename}"
            image_urls.append(url)
            print(f"   ✅ {original_filename} → {final_filename}")
        else:
            print(f"   ❌ Failed: {original_filename}")
    
    return image_urls


def upload_photo_slideshow(image_urls, caption, auto_music=True, to_drafts=True):
    """Upload photo slideshow (carousel) to TikTok using public URLs."""
    
    mode_text = "Drafts (Inbox)" if to_drafts else "Direct Post"
    print(f"\n📸 Uploading photo slideshow ({len(image_urls)} images) → {mode_text}...")
    
    # Create a config file with the data
    config = {
        "image_urls": image_urls,
        "caption": caption,
        "auto_music": auto_music,
        "to_drafts": to_drafts
    }
    
    # Write config to temp file
    config_path = "/tmp/tiktok_photo_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    # Copy config to VM
    subprocess.run([
        "gcloud", "compute", "scp",
        config_path,
        "philosophy-bot-vm:/tmp/tiktok_photo_config.json",
        "--zone=us-central1-a"
    ], capture_output=True)
    
    # Run upload script on VM
    ssh_cmd = """sudo bash -c 'cd /home/runner/philosophy_video_generator && python3 -c "
import requests
import json
from pathlib import Path

# Load config
config = json.load(open(\\"/tmp/tiktok_photo_config.json\\"))
image_urls = config[\\"image_urls\\"]
caption = config[\\"caption\\"]
auto_music = config[\\"auto_music\\"]
to_drafts = config[\\"to_drafts\\"]

# Load tokens
token_file = Path(\\".tiktok_tokens.json\\")
if not token_file.exists():
    print(\\"❌ Not authenticated\\")
    exit(1)

tokens = json.load(open(token_file))
access_token = tokens.get(\\"access_token\\")

headers = {
    \\"Authorization\\": f\\"Bearer {access_token}\\",
    \\"Content-Type\\": \\"application/json; charset=UTF-8\\"
}

# Use MEDIA_UPLOAD for drafts, DIRECT_POST for immediate
post_mode = \\"MEDIA_UPLOAD\\" if to_drafts else \\"DIRECT_POST\\"

init_data = {
    \\"post_info\\": {
        \\"title\\": caption,
        \\"privacy_level\\": \\"SELF_ONLY\\",
        \\"disable_comment\\": False,
        \\"auto_add_music\\": auto_music
    },
    \\"source_info\\": {
        \\"source\\": \\"PULL_FROM_URL\\",
        \\"photo_cover_index\\": 0,
        \\"photo_images\\": image_urls
    },
    \\"post_mode\\": post_mode,
    \\"media_type\\": \\"PHOTO\\"
}

url = \\"https://open.tiktokapis.com/v2/post/publish/content/init/\\"
response = requests.post(url, headers=headers, json=init_data)
result = response.json()

print(f\\"Status: {response.status_code}\\")
print(f\\"Response: {json.dumps(result, indent=2)}\\")

if response.status_code == 200 and result.get(\\"error\\", {}).get(\\"code\\") == \\"ok\\":
    print(\\"\\\\n✅ Photo slideshow sent to drafts!\\")
else:
    print(\\"\\\\n❌ Upload failed\\")
"'"""
    
    cmd = [
        "gcloud", "compute", "ssh",
        "philosophy-bot-vm",
        "--zone=us-central1-a",
        "--command", ssh_cmd
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def upload_video_to_tiktok(video_path, caption):
    """Upload video to TikTok drafts."""
    
    # Copy to VM
    print("📤 Copying video to server...")
    scp_cmd = [
        "gcloud", "compute", "scp",
        video_path,
        "philosophy-bot-vm:/tmp/tiktok_upload.mp4",
        "--zone=us-central1-a"
    ]
    subprocess.run(scp_cmd, capture_output=True)
    
    # Upload via CLI on VM
    print("📤 Uploading to TikTok...")
    
    # Escape quotes in caption
    escaped_caption = caption.replace('"', '\\"').replace("'", "\\'")
    
    ssh_cmd = [
        "gcloud", "compute", "ssh",
        "philosophy-bot-vm",
        "--zone=us-central1-a",
        "--command",
        f"sudo bash -c 'cd /home/runner/philosophy_video_generator && python3 tiktok_cli.py upload --video \"/tmp/tiktok_upload.mp4\" --title \"{escaped_caption}\"'"
    ]
    
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    
    if "Upload successful" in result.stdout:
        print("\n🎉 Video uploaded to TikTok drafts!")
        return True
    else:
        print(f"\n❌ Upload failed")
        if result.stderr:
            print(result.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Upload slideshows to TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Video slideshow (default) - slides combined into video
    python upload_to_tiktok.py --slides "generated_slideshows/gpt15/Stoicism*.png" --caption "#SlideFilm"
    
    # Photo slideshow (native carousel) - each image is swipeable
    python upload_to_tiktok.py --slides "slides/*.png" --mode photo --caption "#SlideFilm"
    
    # Upload existing video
    python upload_to_tiktok.py --video "my_video.mp4" --caption "#SlideFilm"
    
    # Video with custom duration per slide
    python upload_to_tiktok.py --slides "slides/*.png" --duration 7 --caption "#SlideFilm"
        """
    )
    
    parser.add_argument("--slides", type=str, help="Glob pattern for slide images")
    parser.add_argument("--video", type=str, help="Path to existing video file")
    parser.add_argument("--mode", type=str, choices=["video", "photo"], default="video",
                        help="Upload mode: 'video' (default) or 'photo' (native carousel)")
    parser.add_argument("--caption", type=str, default="#SlideFilm", help="Caption (default: #SlideFilm)")
    parser.add_argument("--duration", type=int, default=5, help="Seconds per slide for video mode (default: 5)")
    parser.add_argument("--output", type=str, help="Output video path (video mode only)")
    parser.add_argument("--no-music", action="store_true", help="Don't auto-add music (photo mode only)")
    
    args = parser.parse_args()
    
    if not args.slides and not args.video:
        parser.print_help()
        print("\n❌ Error: Provide either --slides or --video")
        return
    
    if args.video:
        # Upload existing video
        if not os.path.exists(args.video):
            print(f"❌ Video not found: {args.video}")
            return
        upload_video_to_tiktok(args.video, args.caption)
    
    elif args.slides:
        # Find slides
        slide_paths = sorted(glob.glob(args.slides))
        
        if not slide_paths:
            print(f"❌ No slides found matching: {args.slides}")
            return
        
        print(f"📸 Found {len(slide_paths)} slides:")
        for i, s in enumerate(slide_paths):
            print(f"   {i+1}. {Path(s).name}")
        
        if args.mode == "photo":
            # Photo slideshow (native carousel)
            print("\n📱 Mode: Native Photo Slideshow (swipeable)")
            
            # Upload images to server first
            image_urls = upload_images_to_server(slide_paths)
            
            if image_urls:
                upload_photo_slideshow(image_urls, args.caption, auto_music=not args.no_music)
            else:
                print("❌ No images uploaded successfully")
        
        else:
            # Video slideshow
            print("\n🎬 Mode: Video Slideshow")
            
            # Generate output path
            if args.output:
                output_path = args.output
            else:
                base_name = Path(slide_paths[0]).stem.rsplit('_', 1)[0]
                output_path = f"/tmp/{base_name}_tiktok.mp4"
            
            # Create video and upload
            if create_video_from_slides(slide_paths, output_path, args.duration):
                upload_video_to_tiktok(output_path, args.caption)


if __name__ == "__main__":
    main()
