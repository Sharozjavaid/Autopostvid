"""TikTok posting service for automations.

Handles posting photo slideshows to TikTok using the Content Posting API.
Uses PULL_FROM_URL method to fetch images from our verified domain.

IMPORTANT: TikTok only accepts JPEG/WebP format - NOT PNG!
When posting local images, we:
1. Upload to the production server at api.cofndrly.com
2. Server converts PNG → JPEG automatically
3. Use those public URLs for TikTok (domain is verified)
"""
import os
import json
import logging
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Project root for token files
# Path: backend/app/services/tiktok_poster.py -> need 4 parents to get to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/services -> services -> app -> backend -> project root
TOKEN_FILE = PROJECT_ROOT / ".tiktok_tokens.json"

# TikTok API endpoints
PHOTO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

# Base URL for serving images - MUST be api.cofndrly.com (verified in TikTok Developer Portal)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.cofndrly.com")


class TikTokPoster:
    """Posts content to TikTok via the Content Posting API."""
    
    def __init__(self):
        logger.info(f"TikTokPoster init - looking for tokens at: {TOKEN_FILE}")
        self.tokens = self._load_tokens()
        if self.tokens:
            logger.info(f"Tokens loaded: open_id={self.tokens.get('open_id')}, scope={self.tokens.get('scope')}")
        else:
            logger.warning(f"No tokens found at {TOKEN_FILE}")
        
        # Log upload endpoint for debugging
        self._init_gcs()
    
    def _load_tokens(self) -> Optional[dict]:
        """Load TikTok tokens from file."""
        logger.debug(f"Checking token file: {TOKEN_FILE} (exists: {TOKEN_FILE.exists()})")
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE) as f:
                    tokens = json.load(f)
                logger.info(f"Loaded tokens saved at: {tokens.get('saved_at')}")
                return tokens
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")
                return None
        return None
    
    def _init_gcs(self):
        """Initialize storage for uploading local images.
        
        This is needed when running locally because:
        1. Local images aren't accessible via public URLs
        2. TikTok needs to PULL images from public URLs
        3. We upload to the production server at api.cofndrly.com
        
        Note: We now upload to our own server instead of GCS because
        api.cofndrly.com is verified in TikTok Developer Portal.
        """
        # We use HTTP upload to production server instead of GCS
        # The endpoint is /api/tiktok/upload-media
        logger.info(f"TikTok poster will upload images to: {API_BASE_URL}/api/tiktok/upload-media")
    
    def _upload_image_to_server(self, local_path: str) -> Optional[str]:
        """Upload a local image to the production server and return public URL.
        
        The production server at api.cofndrly.com is verified in TikTok Developer Portal,
        so TikTok can pull images from there.
        
        Args:
            local_path: Path to local image file
            
        Returns:
            Public URL of the uploaded JPEG image, or None if failed
        """
        path = Path(local_path)
        if not path.exists():
            logger.error(f"Local image not found: {local_path}")
            return None
        
        try:
            # Read the image file
            with open(path, 'rb') as f:
                file_data = f.read()
            
            # Upload to production server
            upload_url = f"{API_BASE_URL}/api/tiktok/upload-media"
            
            files = {
                'file': (path.name, file_data, 'image/png')
            }
            data = {
                'filename': path.stem
            }
            
            logger.info(f"Uploading {path.name} to {upload_url}...")
            response = requests.post(upload_url, files=files, data=data, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            if result.get("success"):
                # The server returns the full URL
                public_url = result.get("full_url")
                logger.info(f"✅ Uploaded to server: {public_url}")
                return public_url
            else:
                logger.error(f"Upload failed: {result}")
                return None
            
        except Exception as e:
            logger.exception(f"Failed to upload image to server: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid tokens."""
        if not self.tokens or not self.tokens.get("access_token"):
            logger.warning("No access token available")
            return False
        return True
    
    def is_token_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.tokens:
            return True
        
        saved_at = self.tokens.get("saved_at") or self.tokens.get("refreshed_at")
        expires_in = self.tokens.get("expires_in", 86400)  # Default 24 hours
        
        if not saved_at:
            logger.warning("No saved_at timestamp, assuming token may be expired")
            return True
        
        try:
            saved_time = datetime.fromisoformat(saved_at.replace("Z", "+00:00"))
            expiry_time = saved_time + timedelta(seconds=expires_in)
            now = datetime.now(saved_time.tzinfo) if saved_time.tzinfo else datetime.now()
            
            if now > expiry_time:
                logger.warning(f"Token expired at {expiry_time}, current time: {now}")
                return True
            else:
                remaining = (expiry_time - now).total_seconds() / 3600
                logger.info(f"Token valid for {remaining:.1f} more hours")
                return False
        except Exception as e:
            logger.error(f"Error checking token expiry: {e}")
            return True
    
    def ensure_valid_token(self) -> bool:
        """Ensure we have a valid token, refreshing if needed."""
        if not self.is_authenticated():
            logger.error("Not authenticated - no tokens available")
            return False
        
        if self.is_token_expired():
            logger.info("Token expired, attempting refresh...")
            if self.refresh_tokens():
                # Reload tokens after refresh
                self.tokens = self._load_tokens()
                return True
            else:
                logger.error("Token refresh failed")
                return False
        
        return True
    
    def _get_image_url(self, image_path: str) -> Optional[str]:
        """Convert local image path to public URL.
        
        IMPORTANT: TikTok only accepts JPEG or WebP format, NOT PNG.
        
        Strategy:
        1. If it's already a GCS URL (https://storage.googleapis.com/...), use as-is
        2. If it's a local file, upload to GCS as JPEG and return GCS URL
        3. If it's a production path, construct api.cofndrly.com URL
        
        Returns:
            Public URL accessible by TikTok, or None if failed
        """
        # Already a GCS URL
        if image_path.startswith("https://storage.googleapis.com/"):
            # Ensure it's JPEG
            if image_path.endswith('.png'):
                logger.warning(f"GCS URL is PNG, TikTok may reject: {image_path}")
            return image_path
        
        # Already an HTTP URL (assume it's accessible)
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path
        
        path = Path(image_path)
        
        # If it's a local file that exists, upload to production server
        if path.exists():
            logger.info(f"Local file detected, uploading to production server: {image_path}")
            server_url = self._upload_image_to_server(image_path)
            if server_url:
                return server_url
            else:
                logger.error(f"Failed to upload local file to server: {image_path}")
                return None
        
        # It's a relative path that doesn't exist locally - construct production URL
        # This happens when running on production where paths are relative
        jpg_filename = path.stem + ".jpg"
        
        # Check if it's in generated_slideshows (automation-generated)
        if "generated_slideshow" in image_path.lower():
            # Preserve the model subfolder (gpt15, flux, etc.)
            parts = path.parts
            for i, part in enumerate(parts):
                if part == "generated_slideshows" and i + 1 < len(parts):
                    model = parts[i + 1]  # e.g., "gpt15"
                    return f"{API_BASE_URL}/static/slideshows/{model}/{jpg_filename}"
            # Fallback: just use gpt15
            return f"{API_BASE_URL}/static/slideshows/gpt15/{jpg_filename}"
        
        # Also check for direct model paths like "gpt15/" or "flux/"
        if "/gpt15/" in image_path or "/flux/" in image_path or "/dall-e/" in image_path:
            parts = path.parts
            for i, part in enumerate(parts):
                if part in ("gpt15", "flux", "dall-e", "nano"):
                    return f"{API_BASE_URL}/static/slideshows/{part}/{jpg_filename}"
        
        # Frontend project slides (from generated_slides/)
        if "generated_slides" in image_path.lower():
            return f"{API_BASE_URL}/static/slides/{jpg_filename}"
        
        # Default: generated_images - use .jpg for TikTok compatibility
        return f"{API_BASE_URL}/static/images/{jpg_filename}"
    
    def post_photo_slideshow(
        self,
        image_paths: List[str],
        caption: str,
        to_drafts: bool = True,
        photo_cover_index: int = 0
    ) -> dict:
        """Post a photo slideshow to TikTok user's inbox (drafts).
        
        IMPORTANT: We ALWAYS use MEDIA_UPLOAD mode to send to drafts.
        This works with public accounts in sandbox mode.
        NEVER use DIRECT_POST - that requires private accounts in sandbox.
        
        Args:
            image_paths: List of local image paths (will be converted to URLs)
            caption: Caption/title for the post
            to_drafts: Always True - we only post to drafts, never direct
            photo_cover_index: Which image to use as cover (0-indexed)
        
        Returns:
            dict with success status and publish_id or error
        """
        # First ensure we have valid tokens (auto-refresh if expired)
        if not self.ensure_valid_token():
            return {"success": False, "error": "Not authenticated with TikTok. Please re-authorize at /api/tiktok/auth"}
        
        if len(image_paths) < 2:
            return {"success": False, "error": "Need at least 2 images for slideshow"}
        
        if len(image_paths) > 35:
            return {"success": False, "error": "Maximum 35 images allowed"}
        
        # Convert local paths to public URLs (uploads to GCS if local files)
        image_urls = []
        for path in image_paths:
            url = self._get_image_url(path)
            if url is None:
                return {"success": False, "error": f"Failed to get URL for image: {path}"}
            image_urls.append(url)
        
        logger.info(f"Posting {len(image_urls)} images to TikTok DRAFTS (MEDIA_UPLOAD mode)")
        logger.debug(f"Image URLs: {image_urls}")
        
        # Build request payload for DRAFTS (inbox)
        # CRITICAL: Use MEDIA_UPLOAD mode - this sends to user's inbox/drafts
        # NEVER use DIRECT_POST - that requires private accounts in sandbox mode
        payload = {
            "post_info": {
                "title": caption[:90] if caption else "",
                "description": caption[:4000] if caption else ""
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": photo_cover_index,
                "photo_images": image_urls
            },
            "post_mode": "MEDIA_UPLOAD",  # DRAFTS - sends to inbox, user completes in TikTok app
            "media_type": "PHOTO"
        }
        
        headers = {
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        try:
            response = requests.post(PHOTO_INIT_URL, headers=headers, json=payload)
            result = response.json()
            
            logger.info(f"TikTok API response: {result}")
            
            # Check for errors
            error = result.get("error", {})
            if error and error.get("code") != "ok":
                error_code = error.get("code", "unknown")
                error_msg = error.get("message", "Unknown error")
                logger.error(f"TikTok error: {error_code} - {error_msg}")
                return {
                    "success": False,
                    "error": f"{error_code}: {error_msg}",
                    "raw_response": result
                }
            
            # Success
            data = result.get("data", {})
            publish_id = data.get("publish_id")
            
            if publish_id:
                logger.info(f"Successfully initiated post: {publish_id}")
                return {
                    "success": True,
                    "publish_id": publish_id,
                    "status": "processing",
                    "image_count": len(image_urls)
                }
            else:
                return {
                    "success": False,
                    "error": "No publish_id in response",
                    "raw_response": result
                }
            
        except requests.RequestException as e:
            logger.exception(f"Request error: {e}")
            return {"success": False, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def check_post_status(self, publish_id: str) -> dict:
        """Check the status of a pending post.
        
        Returns:
            dict with status info
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        payload = {"publish_id": publish_id}
        
        try:
            response = requests.post(STATUS_URL, headers=headers, json=payload)
            result = response.json()
            
            error = result.get("error", {})
            if error and error.get("code") != "ok":
                return {
                    "success": False,
                    "error": f"{error.get('code')}: {error.get('message')}"
                }
            
            data = result.get("data", {})
            return {
                "success": True,
                "status": data.get("status"),
                "publicaly_available_post_id": data.get("publicaly_available_post_id"),
                "uploaded_bytes": data.get("uploaded_bytes"),
                "fail_reason": data.get("fail_reason")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def refresh_tokens(self) -> bool:
        """Refresh TikTok access token."""
        if not self.tokens or not self.tokens.get("refresh_token"):
            return False
        
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
        
        client_key = os.getenv("TIKTOK_CLIENT_KEY")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        
        if not client_key or not client_secret:
            logger.error("TikTok client credentials not configured")
            return False
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }
        
        data = {
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"]
        }
        
        try:
            response = requests.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle error - can be string or dict
                if "error" in result:
                    error = result.get("error")
                    if isinstance(error, dict):
                        if error.get("code") != "ok":
                            logger.error(f"Token refresh failed: {error}")
                            return False
                    elif isinstance(error, str) and error:
                        logger.error(f"Token refresh failed: {error} - {result.get('error_description', '')}")
                        return False
                
                self.tokens["access_token"] = result.get("access_token", self.tokens["access_token"])
                self.tokens["refresh_token"] = result.get("refresh_token", self.tokens["refresh_token"])
                self.tokens["expires_in"] = result.get("expires_in")
                self.tokens["refreshed_at"] = datetime.now().isoformat()
                
                # Save updated tokens
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(self.tokens, f, indent=2)
                
                logger.info(f"TikTok tokens refreshed successfully, valid for {result.get('expires_in')} seconds")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.exception(f"Token refresh error: {e}")
            return False
