#!/usr/bin/env python3
"""
Instagram CLI - Generate and post slideshows to Instagram via Post Bridge

Usage:
    # Just post existing images
    python instagram_cli.py post --images "img1.png,img2.png" --caption "Caption here"
    
    # Generate and post a slideshow on a topic
    python instagram_cli.py generate --topic "The deadliest men in history" --style "graphic painting"
    
    # Check connection status
    python instagram_cli.py status
    
    # Check post status
    python instagram_cli.py check --post-id "your-post-id"
"""
import os
import sys
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from services.instagram_poster import InstagramPoster, post_slideshow_to_instagram


def cmd_status(args):
    """Check Post Bridge connection status."""
    print("🔍 Checking Post Bridge connection...")
    
    poster = InstagramPoster()
    result = poster.check_connection()
    
    if result.get("success"):
        print(f"✅ Connected to Instagram @{result.get('username')}")
        print(f"   Account ID: {result.get('account_id')}")
        print(f"   Platform: {result.get('platform')}")
    else:
        print(f"❌ Connection failed: {result.get('error')}")
        if result.get("hint"):
            print(f"   💡 {result.get('hint')}")
        if result.get("response"):
            print(f"   Response: {result.get('response')}")
    
    return result.get("success", False)


def cmd_check(args):
    """Check the status of a post."""
    print(f"🔍 Checking post status: {args.post_id}")
    
    poster = InstagramPoster()
    
    # Get post status
    status = poster.get_post_status(args.post_id)
    if status.get("success"):
        print(f"   Status: {status.get('status')}")
        print(f"   Created: {status.get('created_at')}")
    else:
        print(f"❌ Failed to get status: {status.get('error')}")
        return False
    
    # Get post results
    results = poster.get_post_results(args.post_id)
    if results.get("success"):
        post_results = results.get("results", [])
        if post_results:
            print(f"\n📊 Post Results:")
            for r in post_results:
                success_icon = "✅" if r.get("success") else "❌"
                platform_data = r.get("platform_data") or {}
                print(f"   {success_icon} Platform: {platform_data.get('username', 'unknown')}")
                if platform_data.get("url"):
                    print(f"      URL: {platform_data.get('url')}")
                if r.get("error"):
                    print(f"      Error: {r.get('error')}")
        else:
            if status.get("status") == "posted":
                print(f"   ✅ Successfully posted!")
            else:
                print(f"   📊 No results yet (still processing)")
    
    return True


def cmd_post(args):
    """Post images to Instagram."""
    print(f"📸 Posting to Instagram @{args.username or 'philosophizeme_app'}...")
    
    # Parse image paths
    if args.images:
        image_paths = [p.strip() for p in args.images.split(",")]
    else:
        print("❌ No images provided. Use --images 'path1,path2,path3'")
        return False
    
    print(f"   Images: {len(image_paths)} files")
    for path in image_paths:
        exists = os.path.exists(path)
        status = "✅" if exists else "⚠️ (not found locally, assuming URL)"
        print(f"      {status} {path}")
    
    # Parse hashtags
    hashtags = None
    if args.hashtags:
        hashtags = [h.strip().lstrip("#") for h in args.hashtags.split(",")]
    
    # Post to Instagram
    poster = InstagramPoster(username=args.username)
    
    if len(image_paths) == 1:
        result = poster.post_single_image(image_paths[0], args.caption, hashtags)
    else:
        result = poster.post_carousel(image_paths, args.caption, hashtags)
    
    if result.get("success"):
        print(f"✅ Posted successfully!")
        print(f"   Post ID: {result.get('post_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ Post failed: {result.get('error')}")
        if result.get("raw_response"):
            print(f"   Response: {json.dumps(result.get('raw_response'), indent=2)}")
    
    return result.get("success", False)


def cmd_generate(args):
    """Generate a slideshow and optionally post it."""
    print(f"🎨 Generating slideshow: {args.topic}")
    print(f"   Model: {args.model}")
    print(f"   Theme: {args.theme}")
    print(f"   Font: {args.font}")
    
    # Import slideshow generator
    from slideshow_automation import generate_slideshow
    
    # Generate the slideshow
    result = generate_slideshow(
        topic=args.topic,
        model=args.model,
        font_name=args.font,
        theme=args.theme,
        auto_theme=True
    )
    
    if not result.get("success"):
        print(f"❌ Slideshow generation failed: {result.get('error')}")
        return False
    
    print(f"✅ Slideshow generated: {result.get('title')}")
    print(f"   Slides: {result.get('slides_count')}")
    print(f"   Theme: {result.get('theme_name', args.theme)}")
    
    image_paths = result.get("image_paths", [])
    print(f"\n📁 Generated images:")
    for path in image_paths:
        print(f"   {path}")
    
    # Post to Instagram if requested
    if args.post:
        print(f"\n📸 Posting to Instagram...")
        
        # Build caption
        title = result.get("title", args.topic)
        caption = args.caption or f"🔥 {title}"
        
        # Default hashtags for philosophy content
        hashtags = ["philosophy", "history", "wisdom", "stoicism", "motivation", "mindset", "art"]
        if args.hashtags:
            hashtags = [h.strip().lstrip("#") for h in args.hashtags.split(",")]
        
        poster = InstagramPoster(username=args.username)
        post_result = poster.post_carousel(image_paths, caption, hashtags)
        
        if post_result.get("success"):
            print(f"✅ Posted to Instagram!")
            print(f"   Post ID: {post_result.get('post_id')}")
            print(f"   Message: {post_result.get('message')}")
        else:
            print(f"❌ Instagram post failed: {post_result.get('error')}")
            if post_result.get("raw_response"):
                print(f"   Response: {json.dumps(post_result.get('raw_response'), indent=2)}")
            return False
    else:
        print(f"\n💡 To post this slideshow, run:")
        print(f"   python instagram_cli.py post --images \"{','.join(image_paths)}\" --caption \"Your caption\"")
    
    return True


def cmd_generate_and_post(args):
    """Quick command to generate and post in one step."""
    args.post = True
    return cmd_generate(args)


def main():
    parser = argparse.ArgumentParser(
        description="Instagram CLI - Post slideshows via Post Bridge API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check connection
  python instagram_cli.py status
  
  # Generate and post a slideshow
  python instagram_cli.py generate --topic "The 5 deadliest men in history" --post
  
  # Just post existing images
  python instagram_cli.py post --images "slide1.png,slide2.png" --caption "History lesson"
  
  # Generate with custom style
  python instagram_cli.py generate --topic "Ancient warriors" --theme oil_contrast --model gpt15 --post
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check Post Bridge connection")
    
    # Post command
    post_parser = subparsers.add_parser("post", help="Post images to Instagram")
    post_parser.add_argument("--images", "-i", required=True, help="Comma-separated image paths")
    post_parser.add_argument("--caption", "-c", default="", help="Post caption")
    post_parser.add_argument("--hashtags", "-H", help="Comma-separated hashtags")
    post_parser.add_argument("--username", "-u", help="Instagram username (default: philosophizeme_app)")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate slideshow from topic")
    gen_parser.add_argument("--topic", "-t", required=True, help="Topic for the slideshow")
    gen_parser.add_argument("--model", "-m", default="gpt15", choices=["gpt15", "flux"], help="Image model")
    gen_parser.add_argument("--theme", default="oil_contrast", 
                           choices=["auto", "golden_dust", "glitch_titans", "oil_contrast", "scene_portrait"],
                           help="Visual theme")
    gen_parser.add_argument("--font", "-f", default="tiktok-bold", help="Font for text overlay")
    gen_parser.add_argument("--post", "-p", action="store_true", help="Post to Instagram after generating")
    gen_parser.add_argument("--caption", "-c", help="Custom caption (default: uses title)")
    gen_parser.add_argument("--hashtags", "-H", help="Custom hashtags (comma-separated)")
    gen_parser.add_argument("--username", "-u", help="Instagram username (default: philosophizeme_app)")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check post status")
    check_parser.add_argument("--post-id", "-p", required=True, help="Post ID to check")
    
    args = parser.parse_args()
    
    if args.command == "status":
        success = cmd_status(args)
    elif args.command == "post":
        success = cmd_post(args)
    elif args.command == "generate":
        success = cmd_generate(args)
    elif args.command == "check":
        success = cmd_check(args)
    else:
        parser.print_help()
        success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
