#!/usr/bin/env python3
"""
TikTok CLI Tool for Sandbox Testing

This CLI helps you:
1. Authenticate with TikTok OAuth
2. Upload videos to user's draft inbox
3. Check upload status

Usage:
    # Step 1: Get auth URL and authorize
    python tiktok_cli.py auth
    
    # Step 2: Complete auth with the code from redirect
    python tiktok_cli.py token --code "YOUR_AUTH_CODE"
    
    # Step 3: Upload video to drafts
    python tiktok_cli.py upload --video "path/to/video.mp4" --title "Your caption"
    
    # Check status of an upload
    python tiktok_cli.py status --publish-id "PUBLISH_ID"
"""

import argparse
import json
import os
import sys
import requests
import secrets
import hashlib
import base64
import webbrowser
from datetime import datetime
from pathlib import Path


class TikTokCLI:
    """TikTok API client for sandbox testing."""
    
    def __init__(self):
        self._load_env()
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8501")
        
        # API endpoints
        self.auth_base_url = "https://www.tiktok.com/v2/auth/authorize/"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.refresh_token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        
        # Content Posting API v2 endpoints
        self.inbox_init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"  # For drafts
        self.publish_init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"  # For direct publish
        self.status_url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
        
        # Token storage
        self.token_file = Path(__file__).parent / ".tiktok_tokens.json"
        self.pkce_file = Path(__file__).parent / ".tiktok_pkce.json"
        
        self._validate_config()
    
    def _load_env(self):
        """Load .env file."""
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
                    except ValueError:
                        pass
    
    def _validate_config(self):
        """Check if TikTok credentials are configured."""
        if not self.client_key or not self.client_secret:
            print("❌ Error: TikTok credentials not found!")
            print("\nPlease add these to your .env file:")
            print("  TIKTOK_CLIENT_KEY=your_client_key")
            print("  TIKTOK_CLIENT_SECRET=your_client_secret")
            print("  TIKTOK_REDIRECT_URI=your_redirect_uri")
            sys.exit(1)
    
    def generate_pkce_pair(self):
        """Generate PKCE code_verifier and code_challenge."""
        code_verifier = secrets.token_urlsafe(32)
        
        m = hashlib.sha256()
        m.update(code_verifier.encode('ascii'))
        d = m.digest()
        code_challenge = base64.urlsafe_b64encode(d).decode('ascii').rstrip('=')
        
        return code_verifier, code_challenge
    
    def save_pkce(self, code_verifier):
        """Save PKCE verifier for later use."""
        with open(self.pkce_file, 'w') as f:
            json.dump({"code_verifier": code_verifier}, f)
        print(f"💾 PKCE verifier saved to {self.pkce_file}")
    
    def load_pkce(self):
        """Load PKCE verifier."""
        if not self.pkce_file.exists():
            print("❌ No PKCE verifier found. Run 'auth' command first.")
            sys.exit(1)
        with open(self.pkce_file) as f:
            return json.load(f)["code_verifier"]
    
    def save_tokens(self, token_data):
        """Save access and refresh tokens."""
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"💾 Tokens saved to {self.token_file}")
    
    def load_tokens(self):
        """Load saved tokens."""
        if not self.token_file.exists():
            print("❌ No tokens found. Complete OAuth flow first:")
            print("   1. python tiktok_cli.py auth")
            print("   2. python tiktok_cli.py token --code YOUR_CODE")
            sys.exit(1)
        with open(self.token_file) as f:
            return json.load(f)
    
    def cmd_auth(self, open_browser=True):
        """Generate OAuth URL and optionally open browser."""
        code_verifier, code_challenge = self.generate_pkce_pair()
        self.save_pkce(code_verifier)
        
        csrf_state = secrets.token_urlsafe(16)
        
        # Scopes needed for uploads
        # video.upload = upload to inbox (drafts)
        # video.publish = direct publish + photo posts
        scopes = "user.info.basic,video.upload,video.publish"
        
        params = {
            "client_key": self.client_key,
            "scope": scopes,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": csrf_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        # Build URL manually to avoid encoding issues
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{self.auth_base_url}?{param_str}"
        
        print("\n" + "=" * 60)
        print("🔐 TikTok OAuth Authorization")
        print("=" * 60)
        print(f"\n📋 Client Key: {self.client_key}")
        print(f"📋 Redirect URI: {self.redirect_uri}")
        print(f"📋 Scopes: {scopes}")
        print("\n" + "-" * 60)
        print("\n🔗 Authorization URL:")
        print(auth_url)
        print("\n" + "-" * 60)
        
        if open_browser:
            print("\n🌐 Opening browser...")
            webbrowser.open(auth_url)
        
        print("\n📝 After authorizing, you'll be redirected to your redirect URI.")
        print("   Copy the 'code' parameter from the URL and run:")
        print("\n   python tiktok_cli.py token --code YOUR_CODE_HERE")
        print("\n" + "=" * 60)
    
    def cmd_token(self, code):
        """Exchange authorization code for access token."""
        code_verifier = self.load_pkce()
        
        print("\n" + "=" * 60)
        print("🔑 Exchanging Code for Access Token")
        print("=" * 60)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }
        
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }
        
        print(f"📤 Requesting token from: {self.token_url}")
        
        response = requests.post(self.token_url, headers=headers, data=data)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for error in response
            if "error" in result:
                error_info = result.get("error")
                if isinstance(error_info, dict) and error_info.get("code") != "ok":
                    print(f"\n❌ API Error: {error_info}")
                    return
                elif isinstance(error_info, str) and error_info:
                    print(f"\n❌ API Error: {error_info}")
                    print(f"   Description: {result.get('error_description', 'N/A')}")
                    return
            
            # Extract token data
            token_data = {
                "access_token": result.get("access_token"),
                "refresh_token": result.get("refresh_token"),
                "open_id": result.get("open_id"),
                "scope": result.get("scope"),
                "expires_in": result.get("expires_in"),
                "refresh_expires_in": result.get("refresh_expires_in"),
                "token_type": result.get("token_type")
            }
            
            self.save_tokens(token_data)
            
            print("\n✅ Successfully obtained access token!")
            print(f"   Open ID: {token_data['open_id']}")
            print(f"   Scope: {token_data['scope']}")
            print(f"   Expires in: {token_data['expires_in']} seconds")
            print("\n📝 You can now upload videos:")
            print('   python tiktok_cli.py upload --video "path/to/video.mp4" --title "Caption"')
        else:
            print(f"\n❌ Failed to get token: {response.status_code}")
            print(f"   Response: {response.text}")
    
    def cmd_refresh(self):
        """Refresh the access token."""
        tokens = self.load_tokens()
        refresh_token = tokens.get("refresh_token")
        
        if not refresh_token:
            print("❌ No refresh token found. Re-authenticate.")
            sys.exit(1)
        
        print("\n🔄 Refreshing access token...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }
        
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(self.refresh_token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle error - can be string or dict
            if "error" in result:
                error = result.get("error")
                if isinstance(error, dict):
                    if error.get("code") != "ok":
                        print(f"❌ Error: {error}")
                        return
                elif isinstance(error, str) and error:
                    print(f"❌ Error: {error}")
                    print(f"   Description: {result.get('error_description', 'N/A')}")
                    return
            
            tokens["access_token"] = result.get("access_token", tokens["access_token"])
            tokens["refresh_token"] = result.get("refresh_token", tokens["refresh_token"])
            tokens["expires_in"] = result.get("expires_in")
            tokens["refreshed_at"] = datetime.now().isoformat()
            
            self.save_tokens(tokens)
            print("✅ Token refreshed successfully!")
            print(f"   New token expires in: {tokens['expires_in']} seconds")
        else:
            print(f"❌ Failed to refresh: {response.status_code}")
            print(f"   Response: {response.text}")
    
    def cmd_upload(self, video_path, title=None, to_inbox=True):
        """Upload video to TikTok drafts (inbox) or publish directly."""
        tokens = self.load_tokens()
        access_token = tokens.get("access_token")
        
        if not access_token:
            print("❌ No access token found. Complete OAuth flow first.")
            sys.exit(1)
        
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            sys.exit(1)
        
        file_size = video_path.stat().st_size
        
        print("\n" + "=" * 60)
        print("📤 TikTok Video Upload")
        print("=" * 60)
        print(f"📁 File: {video_path}")
        print(f"📊 Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        print(f"📝 Title: {title or '(none)'}")
        print(f"📍 Destination: {'User Inbox (Draft)' if to_inbox else 'Direct Publish'}")
        
        # Choose endpoint based on destination
        if to_inbox:
            init_url = self.inbox_init_url
            # Inbox endpoint doesn't include post_info
            init_data = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1
                }
            }
        else:
            init_url = self.publish_init_url
            init_data = {
                "post_info": {
                    "title": title or "",
                    "privacy_level": "SELF_ONLY",  # Sandbox often requires private
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1
                }
            }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # Step 1: Initialize upload
        print("\n📡 Step 1: Initializing upload...")
        print(f"   URL: {init_url}")
        
        init_response = requests.post(init_url, headers=headers, json=init_data)
        
        print(f"   Status: {init_response.status_code}")
        
        if init_response.status_code != 200:
            print(f"❌ Failed to initialize: {init_response.text}")
            return
        
        init_result = init_response.json()
        print(f"   Response: {json.dumps(init_result, indent=2)}")
        
        if "error" in init_result:
            error_info = init_result.get("error", {})
            if error_info.get("code") != "ok":
                print(f"❌ API Error: {error_info}")
                return
        
        data = init_result.get("data", {})
        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")
        
        if not upload_url:
            print("❌ No upload URL in response")
            return
        
        print(f"\n✅ Got upload URL and publish_id: {publish_id}")
        
        # Step 2: Upload video file
        print("\n📡 Step 2: Uploading video file...")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
        }
        
        upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
        
        print(f"   Status: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201, 202]:
            print("\n✅ Upload successful!")
            print(f"   Publish ID: {publish_id}")
            print("\n📝 Check status with:")
            print(f'   python tiktok_cli.py status --publish-id "{publish_id}"')
            
            if to_inbox:
                print("\n📱 The video should appear in your TikTok app drafts!")
        else:
            print(f"❌ Upload failed: {upload_response.text}")
    
    def cmd_slideshow(self, image_paths, title=None, auto_music=True):
        """Upload photo slideshow (carousel) to TikTok."""
        tokens = self.load_tokens()
        access_token = tokens.get("access_token")
        
        if not access_token:
            print("❌ No access token found. Complete OAuth flow first.")
            sys.exit(1)
        
        # Validate images exist
        valid_images = []
        for img_path in image_paths:
            p = Path(img_path)
            if p.exists():
                valid_images.append(str(p.absolute()))
            else:
                print(f"⚠️  Image not found: {img_path}")
        
        if not valid_images:
            print("❌ No valid images found!")
            sys.exit(1)
        
        if len(valid_images) > 35:
            print("⚠️  TikTok allows max 35 images. Using first 35.")
            valid_images = valid_images[:35]
        
        print("\n" + "=" * 60)
        print("📸 TikTok Photo Slideshow Upload")
        print("=" * 60)
        print(f"📁 Images: {len(valid_images)} photos")
        for i, img in enumerate(valid_images):
            print(f"   {i+1}. {Path(img).name}")
        print(f"📝 Caption: {title or '(none)'}")
        print(f"🎵 Auto-add music: {'Yes' if auto_music else 'No'}")
        
        # For photo slideshows, we need to use PULL_FROM_URL
        # First, we need to upload images to a public URL or use direct upload
        # TikTok's photo API uses URL pulling, so images need to be publicly accessible
        
        # Alternative: Use the content/init endpoint for photos
        content_init_url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # For now, we'll need publicly accessible URLs
        # Let's check if we can use file upload instead
        print("\n⚠️  Note: TikTok photo slideshows require publicly accessible image URLs.")
        print("   For local images, use the --video option to create a video slideshow instead.")
        print("\n   To use photo slideshow, host your images and provide URLs:")
        print("   python tiktok_cli.py slideshow --urls 'https://...1.jpg,https://...2.jpg' --title 'Caption'")
        
        # If URLs are provided (not local files), proceed
        if valid_images[0].startswith('http'):
            init_data = {
                "post_info": {
                    "title": title or "",
                    "privacy_level": "SELF_ONLY",
                    "disable_comment": False,
                    "auto_add_music": auto_music
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_cover_index": 0,
                    "photo_images": valid_images
                },
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO"
            }
            
            print("\n📡 Initializing photo slideshow upload...")
            response = requests.post(content_init_url, headers=headers, json=init_data)
            
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and result.get("error", {}).get("code") == "ok":
                publish_id = result.get("data", {}).get("publish_id")
                print(f"\n✅ Photo slideshow submitted!")
                print(f"   Publish ID: {publish_id}")
            else:
                print(f"\n❌ Upload failed: {result}")
        else:
            print("\n💡 Tip: Use video mode for local images:")
            print(f'   python tiktok_cli.py upload --video "your_video.mp4" --title "{title}"')

    def cmd_status(self, publish_id):
        """Check the status of an upload."""
        tokens = self.load_tokens()
        access_token = tokens.get("access_token")
        
        print("\n" + "=" * 60)
        print("📊 Checking Upload Status")
        print("=" * 60)
        print(f"Publish ID: {publish_id}")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        data = {"publish_id": publish_id}
        
        response = requests.post(self.status_url, headers=headers, json=data)
        
        print(f"\nStatus Code: {response.status_code}")
        
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            status = result.get("data", {}).get("status")
            if status == "PUBLISH_COMPLETE":
                print("\n✅ Video published successfully!")
            elif status == "PROCESSING_DOWNLOAD" or status == "PROCESSING_UPLOAD":
                print("\n⏳ Video is still processing...")
            elif status == "SEND_TO_USER_INBOX":
                print("\n📥 Video sent to user's inbox (drafts)!")
            elif status == "FAILED":
                fail_reason = result.get("data", {}).get("fail_reason")
                print(f"\n❌ Upload failed: {fail_reason}")
            else:
                print(f"\n📋 Status: {status}")
    
    def cmd_info(self):
        """Show current configuration and token status."""
        print("\n" + "=" * 60)
        print("ℹ️  TikTok CLI Configuration")
        print("=" * 60)
        print(f"\n📋 Client Key: {self.client_key}")
        print(f"📋 Client Secret: {self.client_secret[:5]}...{self.client_secret[-3:]}")
        print(f"📋 Redirect URI: {self.redirect_uri}")
        
        if self.token_file.exists():
            tokens = self.load_tokens()
            print(f"\n✅ Tokens found:")
            print(f"   Open ID: {tokens.get('open_id')}")
            print(f"   Scope: {tokens.get('scope')}")
            access_preview = tokens.get('access_token', '')[:20] + "..."
            print(f"   Access Token: {access_preview}")
        else:
            print(f"\n❌ No tokens found at {self.token_file}")
            print("   Run: python tiktok_cli.py auth")


def main():
    parser = argparse.ArgumentParser(
        description="TikTok CLI for Sandbox Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start OAuth flow
    python tiktok_cli.py auth
    
    # Exchange auth code for token
    python tiktok_cli.py token --code "YOUR_CODE"
    
    # Upload video to drafts (inbox)
    python tiktok_cli.py upload --video "video.mp4" --title "My caption"
    
    # Upload and publish directly (requires approval)
    python tiktok_cli.py upload --video "video.mp4" --title "My caption" --publish
    
    # Check upload status
    python tiktok_cli.py status --publish-id "PUBLISH_ID"
    
    # Refresh access token
    python tiktok_cli.py refresh
    
    # Show current config
    python tiktok_cli.py info
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # auth command
    auth_parser = subparsers.add_parser("auth", help="Start OAuth authorization flow")
    auth_parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    # token command
    token_parser = subparsers.add_parser("token", help="Exchange auth code for access token")
    token_parser.add_argument("--code", required=True, help="Authorization code from redirect")
    
    # refresh command
    subparsers.add_parser("refresh", help="Refresh access token")
    
    # upload command
    upload_parser = subparsers.add_parser("upload", help="Upload video to TikTok")
    upload_parser.add_argument("--video", required=True, help="Path to video file")
    upload_parser.add_argument("--title", default="", help="Video caption/title")
    upload_parser.add_argument("--publish", action="store_true", help="Publish directly instead of to drafts")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Check upload status")
    status_parser.add_argument("--publish-id", required=True, help="Publish ID from upload")
    
    # info command
    subparsers.add_parser("info", help="Show current configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = TikTokCLI()
    
    if args.command == "auth":
        cli.cmd_auth(open_browser=not args.no_browser)
    elif args.command == "token":
        cli.cmd_token(args.code)
    elif args.command == "refresh":
        cli.cmd_refresh()
    elif args.command == "upload":
        cli.cmd_upload(args.video, args.title, to_inbox=not args.publish)
    elif args.command == "status":
        cli.cmd_status(args.publish_id)
    elif args.command == "info":
        cli.cmd_info()


if __name__ == "__main__":
    main()
